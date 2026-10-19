"""HTML element construction, attribute validation, and rendering."""

import re
from collections.abc import Callable, Iterable, Mapping
from enum import Enum
from functools import lru_cache
from html import escape
from typing import Protocol, Self, overload


class SupportsHtml(Protocol):
    """Objects that expose already escaped HTML through ``__html__()``."""

    def __html__(self) -> str:
        """Return HTML that can be inserted without further escaping."""
        ...


type Child = str | int | SupportsHtml | None | list[Child] | tuple[Child, ...]
type Attribute = str | int | bool | None

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


class _Missing(Enum):
    CHILD = 0


@lru_cache(maxsize=256)
def _valid_attribute_name(name: str) -> bool:
    return _ATTRIBUTE_NAME.fullmatch(name) is not None


def _render_child(child: Child | Mapping[str, Attribute]) -> str:
    if type(child) is Element:
        return child._html
    if type(child) is str:
        return escape(child, quote=False)
    if child is None:
        return ""
    if type(child) is int:
        return str(child)
    if isinstance(child, _Markup):
        return child._html
    html = getattr(child, "__html__", None)
    if html is not None:
        return str(html())
    if isinstance(child, (str, int)):
        return escape(str(child), quote=False)
    if isinstance(child, (list, tuple)):
        return "".join(
            [item._html if type(item) is Element else _render_child(item) for item in child]
        )
    if isinstance(child, Mapping):
        raise TypeError("Attributes must be the first argument, not a child")
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
        return cls._from_rendered("".join([_render_child(child) for child in children]))

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
    __slots__ = ("attributes", "closing", "name", "opening")

    def __init__(
        self,
        name: str,
        attributes: tuple[tuple[str, Attribute], ...],
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
    return _Tag(tag, (), f"{doctype}<{tag}>", closing)


def _element[E: Element](cls: type[E], tag: _Tag, html: str) -> E:
    """Construct an element from its definition and fully rendered HTML."""
    element = _new(cls)
    element._tag = tag
    element._html = html
    element._count = 0
    return element


class Element(_Markup):
    """An immutable HTML element built from a tag, leading mapping, and children."""

    # Share the tag definition between calls. Most elements store fully rendered HTML.
    # Wrapping a single element stores the child and a run count of identical wrappers
    # instead, so deep nesting avoids copying the child's HTML at every level; the
    # rendered HTML is materialized by __getattr__ the first time it is read.
    __slots__ = ("_count", "_inner", "_tag")
    _tag: _Tag
    _inner: str | Element
    _count: int

    def __getattr__(self, name: str) -> str:
        """Materialize and cache the rendered HTML of an element that wraps a chain."""
        if name != "_html":
            raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")
        openings: list[str] = []
        closings: list[str] = []
        node: str | Element = self
        while not isinstance(node, str):
            tag, count = node._tag, node._count
            openings.append(tag.opening * count)
            closings.append(tag.closing * count)
            node = node._inner
        closings.reverse()
        html = self._html = f"{''.join(openings)}{node}{''.join(closings)}"
        return html

    @overload
    def __new__(cls, tag: str, /, *children: Child) -> Self: ...

    @overload
    def __new__(
        cls, tag: str, attributes: Mapping[str, Attribute], /, *children: Child
    ) -> Self: ...

    def __new__(
        cls,
        tag: str,
        first: Child | Mapping[str, Attribute] | _Missing = _Missing.CHILD,
        /,
        *children: Child,
    ) -> Self:
        """Build an element from a tag, optional leading attributes, and children."""
        if not isinstance(tag, str):
            raise TypeError("HTML tag name must be a string")
        definition = _definition(tag)
        element = _element(cls, definition, f"{definition.opening}{definition.closing}")
        if first is _Missing.CHILD:
            return element
        return element.__call__(first, *children)

    @classmethod
    def _from_content(
        cls,
        _tag: str,
        _attributes: tuple[tuple[str, Attribute], ...] = (),
        _content: str = "",
    ) -> Self:
        """Construct from validated attributes and already escaped content."""
        doctype = "<!doctype html>" if _tag == "html" else ""
        ending = "" if _tag in _VOID_TAGS else f"</{_tag}>"
        attributes = []
        for name, value in _attributes:
            if value is None or value is False:
                continue
            if value is True:
                attributes.append(f" {name}")
            else:
                attributes.append(f' {name}="{escape(str(value), quote=True)}"')
        opening = f"{doctype}<{_tag}{''.join(attributes)}>"
        rendered = f"{opening}{_content}{ending}" if ending else opening
        return _element(cls, _Tag(_tag, _attributes, opening, ending), rendered)

    @overload
    def __call__(self, /, *children: Child) -> Self: ...

    @overload
    def __call__(self, attributes: Mapping[str, Attribute], /, *children: Child) -> Self: ...

    def __call__(
        self,
        first: Child | Mapping[str, Attribute] | _Missing = _Missing.CHILD,
        /,
        *children: Child,
    ) -> Self:
        """Set children, optionally merging attributes from a leading dictionary."""
        definition = self._tag
        if not children and definition.closing:
            if type(first) is str:
                content = escape(first, quote=False)
                rendered = f"{definition.opening}{content}{definition.closing}"
                return _element(type(self), definition, rendered)
            if type(first) is Element:
                # Wrap without copying: extend a run of identical wrappers, link a nested
                # chain, or start a new run around an already rendered child.
                element = _new(type(self))
                element._tag = definition
                if first._count and first._tag is definition:
                    element._inner = first._inner
                    element._count = first._count + 1
                else:
                    element._inner = first if first._count else first._html
                    element._count = 1
                return element
        arguments: tuple[Child | Mapping[str, Attribute], ...] = children
        if first is not _Missing.CHILD:
            arguments = (first, *children)
        attributes = definition.attributes
        # Skip the slow Mapping ABC check for the common string and element first arguments.
        if arguments and (
            isinstance(arguments[0], dict)
            or (type(arguments[0]) not in (str, Element) and isinstance(arguments[0], Mapping))
        ):
            updates = tuple(arguments[0].items())
            for name, value in updates:
                valid = (
                    _valid_attribute_name(name)
                    if type(name) is str
                    else _ATTRIBUTE_NAME.fullmatch(name)
                )
                if not valid:
                    raise ValueError(f"Invalid HTML attribute name: {name!r}")
                if value is not None and not isinstance(value, (str, int, bool)):
                    raise TypeError(f"Unsupported HTML attribute value: {type(value).__name__}")
            if attributes:
                merged = dict(attributes)
                merged.update(updates)
                attributes = tuple(merged.items())
            else:
                attributes = updates
            arguments = arguments[1:]
        if not definition.closing and arguments:
            raise ValueError(f"The {definition.name} element cannot have children")
        if not arguments:
            content = ""
        elif len(arguments) == 1:
            content = _render_child(arguments[0])
        else:
            content = "".join([_render_child(child) for child in arguments])
        if attributes is definition.attributes:
            rendered = (
                f"{definition.opening}{content}{definition.closing}"
                if definition.closing
                else definition.opening
            )
            return _element(type(self), definition, rendered)
        return type(self)._from_content(definition.name, attributes, content)

    def repeat(self, items: Iterable[Child], /) -> Fragment:
        """Render one element per item, reusing attributes and replacing children."""
        definition = self._tag
        if not definition.closing:
            raise ValueError(f"The {definition.name} element cannot have children")
        opening, closing = definition.opening, definition.closing
        parts = []
        for item in items:
            content = escape(item, quote=False) if type(item) is str else _render_child(item)
            parts.extend((opening, content, closing))
        return Fragment._from_rendered("".join(parts))

    def __reduce__(
        self,
    ) -> tuple[Callable[[type[Self], _Tag, str], Self], tuple[type[Self], _Tag, str]]:
        """Return reconstruction data preserving the tag and rendered HTML."""
        return _element, (type(self), self._tag, self._html)
