"""HTML element construction, attribute validation, and rendering."""

import re
from collections.abc import Callable, Iterable, Mapping
from enum import Enum
from functools import lru_cache
from operator import attrgetter, itemgetter
from typing import Any, Protocol, Self

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

# A placeholder renders as its registry index between NUL characters. NUL is not
# escaped and cannot appear in valid HTML, so the marker passes unchanged through every
# render path, which lets a template be built with the ordinary element API and compiled
# by repeat() when it is first filled. Attribute and key accessors share one marker
# each, so building the same template repeatedly does not grow the registry.
_BINDINGS: list[_Getter] = [lambda item: item]
_ATTRIBUTES: dict[str, str] = {}
_KEYS: dict[object, str] = {}
_MARKER = re.compile(r' ([A-Za-z_:][A-Za-z0-9_.:-]*)="\x00(\d+)\x00"|\x00(\d+)\x00')
type _Template = tuple[
    list[str], list[_Getter], list[int], list[tuple[int, Callable[[object], str]]]
]


def _register(getter: _Getter) -> str:
    """Add an accessor to the registry and return its placeholder."""
    _BINDINGS.append(getter)
    return f"\x00{len(_BINDINGS) - 1}\x00"


def bind(accessor: str | _Getter | None = None, /) -> str:
    """Return a placeholder that ``repeat()`` fills from each item.

    A string accessor reads an attribute of the item, including dotted paths, a
    callable receives the item and returns the value, and no accessor uses the
    item itself. The placeholder is a string, so it works as a child, as an
    attribute value, or inside a longer string. ``each`` offers the same
    placeholders through attribute and item access.
    """
    if accessor is None:
        return "\x000\x00"
    if type(accessor) is str:
        marker = _ATTRIBUTES.get(accessor)
        if marker is None:
            marker = _ATTRIBUTES[accessor] = _register(attrgetter(accessor))
        return marker
    if callable(accessor):
        return _register(accessor)
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
        marker = _KEYS.get(key)
        if marker is None:
            marker = _KEYS[key] = _register(itemgetter(key))
        return marker

    def __call__(self, accessor: str | _Getter, /) -> str:
        return bind(accessor)

    def __html__(self) -> str:
        return "\x000\x00"

    def __repr__(self) -> str:
        return "each"


each = _Each()


def _binding(index: str) -> _Getter:
    """Look up a marker's accessor, rejecting markers that no ``bind()`` call produced."""
    try:
        return _BINDINGS[int(index)]
    except IndexError:
        raise ValueError(f"Unknown binding in template: {index}") from None


def _attribute_renderer(name: str, get: _Getter) -> Callable[[object], str]:
    """Render a whole bound attribute per item with the same rules as ``__call__``."""

    def render(item: object) -> str:
        value = get(item)
        if value is None or value is False:
            return ""
        if value is True:
            return f" {name}"
        if type(value) is str:
            return f' {name}="{_escape(value)}"'
        if isinstance(value, (str, int, float)):
            return f' {name}="{_escape(str(value))}"'
        raise TypeError(f"Unsupported HTML attribute value: {type(value).__name__}")

    return render


@lru_cache(maxsize=256)
def _template(html: str) -> _Template:
    """Split template HTML into static pieces and slots for bound values.

    Content getters and whole-attribute renderers retain their separate evaluation
    order; each slot records where its result belongs in the HTML pieces.
    """
    pieces = _MARKER.split(html)
    parts = [pieces[0]]
    getters: list[_Getter] = []
    slots: list[int] = []
    renderers: list[tuple[int, Callable[[object], str]]] = []
    for name, attribute, content, static in zip(
        pieces[1::4], pieces[2::4], pieces[3::4], pieces[4::4]
    ):
        if content is None:
            renderers.append((len(parts), _attribute_renderer(name, _binding(attribute))))
        else:
            getters.append(_binding(content))
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
    for item in items:
        for slot, value in zip(slots, [get(item) for get in getters]):
            parts[slot] = (
                escape(value)
                if type(value) is str
                else str(value)
                if type(value) is int
                else child(value)
            )
        for slot, render in renderers:
            parts[slot] = render(item)
        rendered.append("".join(parts))
    return Fragment._from_rendered("".join(rendered))


def _render_all(children: Iterable[Child]) -> list[str]:
    """Render each child to escaped HTML, handling elements and text inline."""
    return [
        child._html
        if type(child) is Element
        else _escape(child)
        if type(child) is str
        else _render_child(child)
        for child in children
    ]


def _render_child(child: object) -> str:
    if type(child) is Element:
        return child._html
    if type(child) is str:
        return _escape(child)
    if child is None:
        return ""
    if type(child) is int:
        return str(child)
    if isinstance(child, (list, tuple)):
        return "".join(_render_all(child))
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
        return cls._from_rendered("".join(_render_all(children)))

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
        if type(node) is str:
            _, _, opening, closing = self._tag
            count = self._count
            html = self._html = f"{f'{opening}>' * count}{node}{closing * count}"
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
        html = self._html = f"{''.join(openings)}{node}{''.join(closings)}"
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
        if not attributes and not children and closing:
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
                element._html = f"{opening}>{first._html}{closing}"
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
                else:
                    raise TypeError(f"Unsupported HTML attribute value: {type(value).__name__}")
            if len(merged) != len(attributes):
                _duplicate(attributes)
            definition = (tag, merged, opening, closing)
        # A missing first child means no positional children at all. Several children
        # join once with the tags around them, rather than joining and then wrapping,
        # so a large document is written once per level instead of twice.
        if first is _MISSING:
            html = f"{opening}>{closing}"
        elif not closing:
            raise ValueError(f"The {tag} element cannot have children")
        elif children:
            html = "".join(
                [
                    f"{opening}>",
                    *[
                        child._html if type(child) is Element else _render_child(child)
                        for child in (first, *children)
                    ],
                    closing,
                ]
            )
        elif type(first) is str:
            html = f"{opening}>{_escape(first)}{closing}"
        elif type(first) is Element:
            html = f"{opening}>{first._html}{closing}"
        elif isinstance(first, (list, tuple)):
            html = "".join([f"{opening}>", *_render_all(first), closing])
        else:
            html = f"{opening}>{_render_child(first)}{closing}"
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
        if "\x00" in html:
            return _fill(_template(html), items)
        tag, _, opening, closing = self._tag
        if not closing:
            raise ValueError(f"The {tag} element cannot have children")
        contents = [_escape(item) if type(item) is str else _render_child(item) for item in items]
        if not contents:
            return Fragment._from_rendered("")
        # Fold the outer tags into the first and last items so one join writes the result.
        contents[0] = f"{opening}>{contents[0]}"
        contents[-1] = f"{contents[-1]}{closing}"
        return Fragment._from_rendered(f"{closing}{opening}>".join(contents))

    def __reduce__(
        self,
    ) -> tuple[Callable[[type[Self], _Tag, str], Self], tuple[type[Self], _Tag, str]]:
        """Return reconstruction data preserving the tag and rendered HTML."""
        return _element, (type(self), self._tag, self._html)
