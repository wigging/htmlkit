"""HTML element construction, attribute validation, and rendering."""

import re
from collections.abc import Callable, Iterable, Mapping
from enum import Enum
from functools import lru_cache
from itertools import count
from operator import attrgetter, itemgetter
from typing import Any, Protocol, Self
from weakref import WeakValueDictionary

# markupsafe's C escaper visits every character once and returns the same object when
# nothing needs escaping. Calling it directly costs less than any Python wrapper, and a
# single pass never degrades on text dense with special characters.
from markupsafe import _escape_inner as _escape


class SupportsHtml(Protocol):
    """Objects that expose already escaped HTML through ``__html__()``."""

    def __html__(self) -> str:
        """Return HTML that can be inserted without further escaping."""
        ...


type Child = str | int | SupportsHtml | None | list[Child] | tuple[Child, ...]
type Attribute = str | int | float | bool | None

_ATTRIBUTE_NAME = re.compile(r"[A-Za-z_:][A-Za-z0-9_.:-]*")
_TAG_NAME = re.compile(r"[a-z][a-z0-9-]*")
_VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
_new = object.__new__

# Keyword argument names are almost always literals, so map each one seen to its
# normalized, validated attribute name. A dict lookup beats an lru_cache call, and the
# size cap bounds memory when names are generated at runtime.
_ATTRIBUTE_NAMES: dict[str, str] = {}
_ATTRIBUTE_NAME_LIMIT = 1024


class _Missing(Enum):
    CHILD = 0


_MISSING = _Missing.CHILD


def _attribute_name(keyword: str) -> str:
    """Normalize a keyword into an attribute name, validating and caching it."""
    name = keyword.removesuffix("_").replace("_", "-")
    if not _ATTRIBUTE_NAME.fullmatch(name):
        raise ValueError(f"Invalid HTML attribute name: {name!r}")
    name = name.lower()
    if len(_ATTRIBUTE_NAMES) < _ATTRIBUTE_NAME_LIMIT:
        _ATTRIBUTE_NAMES[keyword] = name
    return name


def _duplicate(attributes: Mapping[str, Attribute]) -> None:
    """Raise for the first pair of keywords that normalize to the same attribute name."""
    seen: set[str] = set()
    for keyword in attributes:
        name = _attribute_name(keyword)
        if name in seen:
            raise TypeError(f"Duplicate HTML attribute: {name!r}")
        seen.add(name)


type _Getter = Callable[[Any], object]

# NUL-delimited markers survive escaping. Their IDs are never reused, and the
# accessor caches are weak: placeholder strings and templates own the bindings.
_BINDING_IDS = count()
_ATTRIBUTES: WeakValueDictionary[str, _Binding] = WeakValueDictionary()
# Cache by identity so an arbitrary key cannot root its own template through this
# registry. The live binding's itemgetter keeps the key (and its identity) alive.
_KEYS: WeakValueDictionary[int, _Binding] = WeakValueDictionary()
_PLACEHOLDER = re.compile(r"\x00(\d+)\x00")
_MARKER = re.compile(r' ([A-Za-z_:][A-Za-z0-9_.:-]*)="([^"]*\x00\d+\x00[^"]*)"|\x00(\d+)\x00')
_LOST_BINDING = "Binding references were lost; use + or format inside a binding callback"
type _Template = tuple[
    list[str], list[_Getter], list[int], list[tuple[int, Callable[[object], str]]]
]


class _Binding:
    """An accessor owned by the strings containing its marker."""

    __slots__ = ("__weakref__", "get", "marker")

    def __init__(self, getter: _Getter) -> None:
        self.get = getter
        index = str(next(_BINDING_IDS))
        self.marker = f"\x00{index}\x00"


_ITEM = _Binding(lambda item: item)


class _BoundString(str):
    """String content that owns its bindings and its compiled template."""

    __slots__ = ("_bindings", "_template")
    _bindings: tuple[_Binding, ...]
    _template: _Template | None

    def __new__(cls, html: str, bindings: tuple[_Binding, ...]) -> Self:
        value = super().__new__(cls, html)
        value._bindings = bindings
        value._template = None
        return value

    def __str__(self) -> str:
        return self

    def __add__(self, other: str) -> str:
        bindings = self._bindings
        if isinstance(other, _BoundString):
            bindings = tuple(set(bindings).union(other._bindings))
        return _BoundString(str.__add__(self, other), bindings)

    def __radd__(self, other: str) -> str:
        return _BoundString(str.__add__(other, self), self._bindings)

    def __copy__(self) -> Self:
        """Share immutable text and its binding ownership when copied."""
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        # Like ordinary strings, copies share content. In particular, do not clone
        # a callback's captured state or an instance owning a bound method.
        return self


def _join(parts: list[str], separator: str = "") -> str:
    """Join pieces, propagating binding ownership without scanning their text."""
    html = separator.join(parts)
    bindings = {
        binding for part in parts if type(part) is _BoundString for binding in part._bindings
    }
    return _BoundString(html, tuple(bindings)) if bindings else html


def bind(accessor: str | _Getter | None = None, /) -> str:
    """Return a placeholder that ``repeat()`` fills from each item.

    A string accessor reads an attribute of the item, including dotted paths, a
    callable receives the item and returns the value, and no accessor uses the
    item itself. The placeholder is a string, so it works as a child, as an
    attribute value, or inside a longer string built with ``+``. Keep this string
    or its template alive to retain the accessor. ``each`` offers the same
    placeholders through attribute and item access.
    """
    if accessor is None:
        return _BoundString(_ITEM.marker, (_ITEM,))
    if type(accessor) is str:
        binding = _ATTRIBUTES.get(accessor)
        if binding is None:
            binding = _ATTRIBUTES[accessor] = _Binding(attrgetter(accessor))
        return _BoundString(binding.marker, (binding,))
    if callable(accessor):
        binding = _Binding(accessor)
        return _BoundString(binding.marker, (binding,))
    raise TypeError(f"Unsupported binding accessor: {type(accessor).__name__}")


class _Each:
    """The item being rendered by ``repeat()``, expressed through placeholders.

    ``each.name`` reads an attribute of the item, ``each[key]`` indexes it,
    ``each(accessor)`` is ``bind(accessor)``, and ``each`` by itself is the item.
    """

    __slots__ = ()

    def __getattr__(self, name: str) -> str:
        if name.startswith("__"):
            raise AttributeError(f"'each' object has no attribute {name!r}")
        return bind(name)

    def __getitem__(self, key: object) -> str:
        binding = _KEYS.get(id(key))
        if binding is None:
            binding = _KEYS[id(key)] = _Binding(itemgetter(key))
        return _BoundString(binding.marker, (binding,))

    def __call__(self, accessor: str | _Getter, /) -> str:
        return bind(accessor)

    def __html__(self) -> str:
        return _BoundString(_ITEM.marker, (_ITEM,))

    def __repr__(self) -> str:
        return "each"


each = _Each()


def _binding(index: str, bindings: dict[str, _Getter]) -> _Getter:
    """Look up a marker in the bindings owned by this template."""
    try:
        return bindings[index]
    except KeyError:
        raise ValueError(_LOST_BINDING) from None


def _attribute_renderer(
    name: str | None, index: str, bindings: dict[str, _Getter]
) -> Callable[[object], str]:
    """Render a whole attribute or an interpolated value, never as child HTML."""
    get = _binding(index, bindings)
    if name is None:

        def interpolate(item: object) -> str:
            value = get(item)
            if type(value) is str:
                return _escape(value)
            if value is None:
                return ""
            if isinstance(value, (str, int, float)):
                escaped = _escape(str(value))
                return (
                    _BoundString(escaped, value._bindings)
                    if type(value) is _BoundString
                    else escaped
                )
            raise TypeError(f"Unsupported HTML attribute value: {type(value).__name__}")

        return interpolate

    def render(item: object) -> str:
        value = get(item)
        if value is None or value is False:
            return ""
        if value is True:
            return f" {name}"
        if type(value) is str:
            return f' {name}="{_escape(value)}"'
        if isinstance(value, (str, int, float)):
            html = f' {name}="{_escape(str(value))}"'
            return _BoundString(html, value._bindings) if type(value) is _BoundString else html
        raise TypeError(f"Unsupported HTML attribute value: {type(value).__name__}")

    return render


def _template(html: _BoundString) -> _Template:
    """Split template HTML into static pieces and slots for bound values.

    Content getters and attribute renderers retain their separate evaluation
    order; each slot records where its result belongs in the HTML pieces.
    """
    bindings = {binding.marker[1:-1]: binding.get for binding in html._bindings}
    pieces = _MARKER.split(html)
    parts = [pieces[0]]
    getters: list[_Getter] = []
    slots: list[int] = []
    renderers: list[tuple[int, Callable[[object], str]]] = []
    for name, attribute, content, static in zip(
        pieces[1::4], pieces[2::4], pieces[3::4], pieces[4::4]
    ):
        if content is None:
            values = _PLACEHOLDER.split(attribute)
            if len(values) == 3 and not values[0] and not values[2]:
                renderers.append((len(parts), _attribute_renderer(name, values[1], bindings)))
            else:
                # Literal attribute text is already escaped. Keep it in the row's
                # static pieces so interpolation needs no per-attribute list or join.
                parts[-1] += f' {name}="{values[0]}'
                for index, suffix in zip(values[1::2], values[2::2]):
                    renderers.append((len(parts), _attribute_renderer(None, index, bindings)))
                    parts.extend(("", suffix))
                parts[-1] += '"' + static
                continue
        else:
            getters.append(_binding(content, bindings))
            slots.append(len(parts))
        parts.extend(("", static))
    return parts, getters, slots, renderers


def _fill(template: _Template, items: Iterable[object]) -> Fragment:
    """Render a compiled template once per item in a single pass."""
    parts, getters, slots, renderers = template
    # Reuse slots across rows, but never mutate the cached template: a callback may
    # fill the same template recursively while this render is still in progress.
    parts = parts.copy()
    rendered: list[str] = []
    escape = _escape
    child = _render_child
    bound_rows = False
    for item in items:
        bound = False
        for slot, value in zip(slots, [get(item) for get in getters]):
            if type(value) is str:
                parts[slot] = escape(value)
            elif type(value) is int:
                parts[slot] = str(value)
            else:
                parts[slot] = content = child(value)
                if type(content) is _BoundString:
                    bound = True
        for slot, render in renderers:
            parts[slot] = content = render(item)
            if type(content) is _BoundString:
                bound = True
        if bound:
            rendered.append(_join(parts))
            bound_rows = True
        else:
            rendered.append("".join(parts))
    return Fragment._from_rendered(_join(rendered) if bound_rows else "".join(rendered))


def _render_all(children: Iterable[object]) -> tuple[list[str], bool]:
    """Render children and flag bound pieces without scanning their text."""
    parts = [
        child._html
        if type(child) is Element
        else _escape(child)
        if type(child) is str
        else _render_child(child)
        for child in children
    ]
    for part in parts:
        if type(part) is _BoundString:
            return parts, True
    return parts, False


def _render_child(child: object) -> str:
    if type(child) is Element:
        return child._html
    if type(child) is str:
        return _escape(child)
    if isinstance(child, _BoundString):
        return _BoundString(_escape(child), child._bindings)
    if child is None:
        return ""
    if type(child) is int:
        return str(child)
    if isinstance(child, (list, tuple)):
        parts, bound = _render_all(child)
        return _join(parts) if bound else "".join(parts)
    if isinstance(child, _Markup):
        return child._html
    html = getattr(child, "__html__", None)
    if html is not None:
        return str(html())
    if isinstance(child, (str, int)):
        return _render_child(str(child))
    if isinstance(child, Mapping):
        raise TypeError("Pass attributes as keywords, not dictionaries")
    raise TypeError(f"Unsupported HTML child: {type(child).__name__}")


class _Markup:
    """Base for immutable objects that hold already rendered HTML."""

    __slots__ = ("_html",)
    _html: str

    def __str__(self) -> str:
        return self._html

    def __html__(self) -> str:
        return self._html

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._html!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return other._html == self._html

    def __hash__(self) -> int:
        return hash((type(self), self._html))

    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        """Encode rendered HTML, using UTF-8 by default."""
        return self._html.encode(encoding, errors)


class Raw(_Markup):
    """Trusted HTML inserted without escaping.

    Use only for markup the application controls, such as inline scripts and
    styles. The content is never validated or sanitized.
    """

    __slots__ = ()

    def __new__(cls, html: str, /) -> Self:
        """Wrap a trusted string without validating or escaping its content."""
        if not isinstance(html, str):
            raise TypeError("Raw HTML must be a string")
        raw = _new(cls)
        raw._html = html
        return raw

    def __reduce__(self) -> tuple[type[Self], tuple[str]]:
        """Return reconstruction data preserving the trusted HTML."""
        return type(self), (self._html,)


class Fragment(_Markup):
    """An immutable group of escaped children without a wrapping tag."""

    __slots__ = ()

    def __new__(cls, *children: Child) -> Self:
        """Snapshot children as escaped HTML without a wrapping tag."""
        return cls.from_iterable(children)

    @classmethod
    def from_iterable(cls, children: Iterable[Child], /) -> Self:
        """Immediately consume children and snapshot their escaped HTML."""
        parts, bound = _render_all(children)
        return cls._from_rendered(_join(parts) if bound else "".join(parts))

    @classmethod
    def _from_rendered(cls, rendered: str) -> Self:
        """Construct from already escaped HTML."""
        fragment = _new(cls)
        fragment._html = rendered
        return fragment

    def __reduce__(self) -> tuple[Callable[[str], Self], tuple[str]]:
        """Return reconstruction data that avoids escaping the fragment again."""
        return type(self)._from_rendered, (self._html,)


# A tag definition is the tuple ``(name, attributes, opening, closing)``: the validated
# tag name, its normalized attributes, the opening tag without its final ``>`` so that
# rendering can append the content in one string build, and the closing tag, which is
# empty for void elements. A plain tuple builds and unpacks faster than any class, and
# the attributes dict is shared between elements and never mutated after creation.
type _Tag = tuple[str, dict[str, Attribute], str, str]


def _opening(tag: str) -> str:
    """Return the start of an opening tag, prefixing the document element's doctype."""
    return "<!doctype html><html" if tag == "html" else f"<{tag}"


@lru_cache(maxsize=256)
def _definition(tag: str) -> _Tag:
    """Validate a tag name and build its attribute-free definition."""
    if not _TAG_NAME.fullmatch(tag):
        raise ValueError(f"Invalid HTML tag name: {tag!r}")
    return tag, {}, _opening(tag), "" if tag in _VOID_TAGS else f"</{tag}>"


def _element[E: Element](cls: type[E], tag: _Tag, html: str) -> E:
    """Construct an element from its definition and fully rendered HTML."""
    element = _new(cls)
    element._tag = tag
    element._html = html
    element._count = 0
    return element


class Element(_Markup):
    """An immutable HTML element built from a tag, children, and keyword attributes."""

    # Share the tag definition between calls. Most elements store fully rendered HTML.
    # Wrapping a single element in a run of identical tags, or wrapping such a run,
    # stores the child and a run count instead, so deep nesting avoids copying the
    # child's HTML at every level; the rendered HTML is materialized by __getattr__
    # the first time it is read.
    __slots__ = ("_count", "_inner", "_tag")
    _tag: _Tag
    _inner: str | Element
    _count: int

    def __getattr__(self, name: str) -> str:
        """Materialize and cache the rendered HTML of an element that wraps a chain."""
        if name != "_html":
            raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")
        node: str | Element = self._inner
        if isinstance(node, str):
            _, _, opening, closing = self._tag
            count = self._count
            html = f"{f'{opening}>' * count}{node}{closing * count}"
            if type(node) is _BoundString:
                html = _BoundString(html, node._bindings)
            self._html = html
            return html
        openings: list[str] = []
        closings: list[str] = []
        node = self
        while not isinstance(node, str):
            _, _, opening, closing = node._tag
            count = node._count
            openings.append(f"{opening}>" * count)
            closings.append(closing * count)
            node = node._inner
        closings.reverse()
        html = f"{''.join(openings)}{node}{''.join(closings)}"
        if type(node) is _BoundString:
            html = _BoundString(html, node._bindings)
        self._html = html
        return html

    def __new__(
        cls,
        tag: str,
        /,
        *children: Child,
        **attributes: Attribute,
    ) -> Self:
        """Build an element from a tag, children, and keyword attributes."""
        if not isinstance(tag, str):
            raise TypeError("HTML tag name must be a string")
        definition = _definition(tag)
        _, _, opening, closing = definition
        element = _element(cls, definition, f"{opening}>{closing}")
        if not children and not attributes:
            return element
        return element.__call__(*children, **attributes)

    def __call__(
        self,
        first: Child | _Missing = _MISSING,
        /,
        *children: Child,
        **attributes: Attribute,
    ) -> Self:
        """Replace children and merge keyword attributes.

        Attribute names lose one trailing underscore and replace remaining
        underscores with hyphens, such as ``class_`` and ``aria_label``, then
        become lowercase.
        """
        definition = self._tag
        tag, base, opening, closing = definition
        if not attributes and not children and closing and type(opening) is str:
            if type(first) is str:
                element = _new(type(self))
                element._tag = definition
                element._html = f"{opening}>{_escape(first)}{closing}"
                element._count = 0
                return element
            if type(first) is Element:
                # Extend a run of identical wrappers, or start one around a flat element
                # with the same tag, without copying the child's HTML.
                count = first._count
                if first._tag is definition:
                    element = _new(type(self))
                    element._tag = definition
                    element._inner = first._inner if count else first._html
                    element._count = count + 1
                    return element
                element = _new(type(self))
                element._tag = definition
                if count:
                    # Link a chain of other tags; its HTML is materialized when read.
                    element._inner = first
                    element._count = 1
                    return element
                inner = first._html
                html = f"{opening}>{inner}{closing}"
                element._html = (
                    _BoundString(html, inner._bindings) if type(inner) is _BoundString else html
                )
                element._count = 0
                return element
            if type(first) is int:
                element = _new(type(self))
                element._tag = definition
                element._html = f"{opening}>{first}{closing}"
                element._count = 0
                return element
        if attributes:
            names = _ATTRIBUTE_NAMES
            merged: dict[str, Attribute] = {}
            bindings: set[_Binding] | None = None
            if base:
                # Normalize the new keywords first so they override the inherited
                # entries in place, then render the whole set from the bare tag.
                for keyword, value in attributes.items():
                    merged[names.get(keyword) or _attribute_name(keyword)] = value
                if len(merged) != len(attributes):
                    _duplicate(attributes)
                merged = base | merged
                attributes = merged
                opening = _opening(tag)
            # Inherited names are already normalized. Fresh attributes are normalized
            # while growing the opening tag, avoiding a separate pass.
            for keyword, value in attributes.items():
                if base:
                    name = keyword
                else:
                    name = names.get(keyword) or _attribute_name(keyword)
                    merged[name] = value
                if value is None or value is False:
                    continue
                if value is True:
                    opening = f"{opening} {name}"
                elif type(value) is str:
                    opening = f'{opening} {name}="{_escape(value)}"'
                elif isinstance(value, (str, int, float)):
                    opening = f'{opening} {name}="{_escape(str(value))}"'
                    if type(value) is _BoundString:
                        if bindings is None:
                            bindings = set(value._bindings)
                        else:
                            bindings.update(value._bindings)
                else:
                    raise TypeError(f"Unsupported HTML attribute value: {type(value).__name__}")
            if len(merged) != len(attributes):
                _duplicate(attributes)
            if bindings:
                opening = _BoundString(opening, tuple(bindings))
            definition = (tag, merged, opening, closing)
        # A missing first child means no positional children at all. Several children
        # join once with the tags around them, rather than joining and then wrapping,
        # so a large document is written once per level instead of twice.
        if first is _MISSING:
            html = f"{opening}>{closing}"
        elif not closing:
            raise ValueError(f"The {tag} element cannot have children")
        elif children:
            parts = [opening + ">"]
            bound = type(opening) is _BoundString
            for child in (first, *children):
                content = child._html if type(child) is Element else _render_child(child)
                if type(content) is _BoundString:
                    bound = True
                parts.append(content)
            parts.append(closing)
            html = _join(parts) if bound else "".join(parts)
        elif type(first) is str:
            html = f"{opening}>{_escape(first)}{closing}"
        elif isinstance(first, (list, tuple)):
            parts, bound = _render_all(first)
            parts.insert(0, opening + ">")
            parts.append(closing)
            html = _join(parts) if bound or type(opening) is _BoundString else "".join(parts)
        else:
            content = first._html if type(first) is Element else _render_child(first)
            html = (
                _join([opening, ">", content, closing])
                if type(content) is _BoundString
                else f"{opening}>{content}{closing}"
            )
        if type(opening) is _BoundString and type(html) is str:
            html = _BoundString(html, opening._bindings)
        element = _new(type(self))
        element._tag = definition
        element._html = html
        element._count = 0
        return element

    def repeat(self, items: Iterable[object], /) -> Fragment:
        """Render one element per item.

        An element containing ``bind()`` placeholders is a template: each item
        fills its placeholders, and a whole bound attribute follows the usual
        rules for ``None``, ``False``, and ``True``. Without placeholders, each
        item replaces the children and the attributes are reused.
        """
        html = self._html
        if isinstance(html, _BoundString):
            if html._template is None:
                html._template = _template(html)
            return _fill(html._template, items)
        if "\x00" in html and _PLACEHOLDER.search(html):
            raise ValueError(_LOST_BINDING)
        tag, _, opening, closing = self._tag
        if not closing:
            raise ValueError(f"The {tag} element cannot have children")
        contents: list[str] = []
        bound = False
        escape = _escape
        for item in items:
            if type(item) is str:
                contents.append(escape(item))
            else:
                content = _render_child(item)
                if type(content) is _BoundString:
                    bound = True
                contents.append(content)
        if not contents:
            return Fragment._from_rendered("")
        # Fold the outer tags into the first and last items so one join writes the result.
        contents[0] = f"{opening}>" + contents[0]
        contents[-1] = contents[-1] + closing
        separator = f"{closing}{opening}>"
        return Fragment._from_rendered(
            _join(contents, separator) if bound else separator.join(contents)
        )

    def __reduce__(
        self,
    ) -> tuple[Callable[[type[Self], _Tag, str], Self], tuple[type[Self], _Tag, str]]:
        """Return reconstruction data preserving the tag and rendered HTML."""
        return _element, (type(self), self._tag, self._html)
