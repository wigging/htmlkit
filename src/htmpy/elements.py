"""HTML element construction, attribute validation, and rendering."""

import re
from collections.abc import Callable, Iterable, Mapping
from enum import Enum
from functools import lru_cache
from typing import Protocol, Self

from markupsafe import _escape_inner


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


# markupsafe's C escaper visits every character once, which wins for short strings and
# for text dense with special characters. For longer text the ``in`` checks use a
# vectorized scan and skip str.replace for characters that are absent, so clean prose
# costs a few scans rather than a per-character loop. The threshold is the measured
# crossover for clean text on CPython 3.14.
_LONG_TEXT = 64


def _escape(text: str) -> str:
    """Escape ``&``, ``<``, ``>``, ``"``, and ``'`` as markupsafe does."""
    if len(text) < _LONG_TEXT:
        return _escape_inner(text)
    if "&" in text:
        text = text.replace("&", "&amp;")
    if "<" in text:
        text = text.replace("<", "&lt;")
    if ">" in text:
        text = text.replace(">", "&gt;")
    if '"' in text:
        text = text.replace('"', "&#34;")
    if "'" in text:
        text = text.replace("'", "&#39;")
    return text


def _render_child(child: Child) -> str:
    if type(child) is Element:
        return child._html
    if type(child) is str:
        return _escape(child)
    if child is None:
        return ""
    if type(child) is int:
        return str(child)
    if isinstance(child, (list, tuple)):
        return "".join(
            [item._html if type(item) is Element else _render_child(item) for item in child]
        )
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
        return cls._from_rendered(
            "".join(
                [
                    child._html if type(child) is Element else _render_child(child)
                    for child in children
                ]
            )
        )

    @classmethod
    def _from_rendered(cls, rendered: str) -> Self:
        """Construct from already escaped HTML."""
        fragment = _new(cls)
        fragment._html = rendered
        return fragment

    def __reduce__(self) -> tuple[Callable[[str], Self], tuple[str]]:
        """Return reconstruction data that avoids escaping the fragment again."""
        return type(self)._from_rendered, (self._html,)


class _Tag:
    """A validated tag name with its attributes and rendered opening and closing tags."""

    # Slots read faster than named tuple fields on the element construction path.
    # The attributes dict is shared between elements and never mutated after creation.
    __slots__ = ("attributes", "closing", "name", "opening")

    def __init__(
        self,
        name: str,
        attributes: dict[str, Attribute],
        opening: str,
        closing: str,
    ) -> None:
        self.name = name
        self.attributes = attributes
        self.opening = opening
        self.closing = closing


@lru_cache(maxsize=256)
def _definition(tag: str) -> _Tag:
    """Validate a tag name and build its attribute-free definition."""
    if not _TAG_NAME.fullmatch(tag):
        raise ValueError(f"Invalid HTML tag name: {tag!r}")
    doctype = "<!doctype html>" if tag == "html" else ""
    closing = "" if tag in _VOID_TAGS else f"</{tag}>"
    return _Tag(tag, {}, f"{doctype}<{tag}>", closing)


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
            tag, count = self._tag, self._count
            html = self._html = f"{tag.opening * count}{node}{tag.closing * count}"
            return html
        openings: list[str] = []
        closings: list[str] = []
        node = self
        while not isinstance(node, str):
            tag, count = node._tag, node._count
            openings.append(tag.opening * count)
            closings.append(tag.closing * count)
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
        element = _element(cls, definition, f"{definition.opening}{definition.closing}")
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
        closing = definition.closing
        if not children and not attributes and closing:
            if type(first) is str:
                element = _new(type(self))
                element._tag = definition
                element._html = f"{definition.opening}{_escape(first)}{closing}"
                element._count = 0
                return element
            if type(first) is Element:
                # Extend a run of identical wrappers, or start one around a flat element
                # with the same tag, without copying the child's HTML.
                tag, count = first._tag, first._count
                if tag is definition:
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
                element._html = f"{definition.opening}{first._html}{closing}"
                element._count = 0
                return element
            if type(first) is int:
                element = _new(type(self))
                element._tag = definition
                element._html = f"{definition.opening}{first}{closing}"
                element._count = 0
                return element
        if attributes:
            names = _ATTRIBUTE_NAMES
            merged: dict[str, Attribute] = {}
            for keyword, value in attributes.items():
                name = names.get(keyword)
                if name is None:
                    name = _attribute_name(keyword)
                merged[name] = value
            if len(merged) != len(attributes):
                # Two keywords collapsed onto one name; find it for the error message.
                seen: set[str] = set()
                for keyword in attributes:
                    name = _attribute_name(keyword)
                    if name in seen:
                        raise TypeError(f"Duplicate HTML attribute: {name!r}")
                    seen.add(name)
            base = definition.attributes
            if base:
                merged = base | merged
            tag = definition.name
            # Grow the opening tag in place; for a handful of attributes this beats
            # collecting parts and joining them.
            opening = f"<!doctype html><{tag}" if tag == "html" else f"<{tag}"
            for name, value in merged.items():
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
            # Fill the slots directly; calling _Tag.__init__ costs as much as the rest.
            definition = _new(_Tag)
            definition.name = tag
            definition.attributes = merged
            definition.opening = f"{opening}>"
            definition.closing = closing
        # A missing first child means no positional children at all.
        if first is _MISSING:
            content = ""
        elif not closing:
            raise ValueError(f"The {definition.name} element cannot have children")
        elif children:
            content = "".join(
                [
                    child._html if type(child) is Element else _render_child(child)
                    for child in (first, *children)
                ]
            )
        else:
            content = first._html if type(first) is Element else _render_child(first)
        element = _new(type(self))
        element._tag = definition
        element._html = f"{definition.opening}{content}{closing}" if closing else definition.opening
        element._count = 0
        return element

    def repeat(self, items: Iterable[Child], /) -> Fragment:
        """Render one element per item, reusing attributes and replacing children."""
        definition = self._tag
        if not definition.closing:
            raise ValueError(f"The {definition.name} element cannot have children")
        contents = []
        for item in items:
            contents.append(_escape(item) if type(item) is str else _render_child(item))
        if not contents:
            return Fragment._from_rendered("")
        opening, closing = definition.opening, definition.closing
        return Fragment._from_rendered(f"{opening}{f'{closing}{opening}'.join(contents)}{closing}")

    def __reduce__(
        self,
    ) -> tuple[Callable[[type[Self], _Tag, str], Self], tuple[type[Self], _Tag, str]]:
        """Return reconstruction data preserving the tag and rendered HTML."""
        return _element, (type(self), self._tag, self._html)
