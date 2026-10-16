"""HTML element construction, attribute validation, and rendering."""

import re
from collections.abc import Callable, Iterable, Mapping
from enum import Enum
from functools import lru_cache
from html import escape
from typing import NamedTuple, Self, overload

type Child = str | int | Element | _Fragment | None | list[Child] | tuple[Child, ...]
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


class _Missing(Enum):
    CHILD = 0


@lru_cache(maxsize=256)
def _valid_attribute_name(name: str) -> bool:
    return _ATTRIBUTE_NAME.fullmatch(name) is not None


def _render_child(child: Child | Mapping[str, Attribute]) -> str:
    if type(child) is Element:
        return child[1]
    if type(child) is str:
        return escape(child, quote=False)
    if child is None:
        return ""
    if isinstance(child, (Element, _Fragment)):
        return str(child)
    if isinstance(child, (str, int)):
        return escape(str(child), quote=False)
    if isinstance(child, (list, tuple)):
        return "".join(
            [item[1] if type(item) is Element else _render_child(item) for item in child]
        )
    if isinstance(child, Mapping):
        raise TypeError("Attributes must be the first argument, not a child")
    raise TypeError(f"Unsupported HTML child: {type(child).__name__}")


class _Fragment(NamedTuple):
    """Already escaped HTML produced by repeating an element."""

    rendered: str

    def __str__(self) -> str:
        return self.rendered


class _Tag(NamedTuple):
    name: str
    attributes: tuple[tuple[str, Attribute], ...]
    opening: str
    closing: str


class Element(tuple[_Tag, str]):
    """An immutable HTML element built from a tag, leading mapping, and children."""

    # Share the tag definition between calls; store fully rendered HTML per element.
    __slots__ = ()

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
        if not isinstance(tag, str):
            raise TypeError("HTML tag name must be a string")
        if not _TAG_NAME.fullmatch(tag):
            raise ValueError(f"Invalid HTML tag name: {tag!r}")
        element: Self = cls._from_content(tag)
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
        return tuple.__new__(cls, (_Tag(_tag, _attributes, opening, ending), rendered))

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
        definition = self[0]
        if type(first) is str and not children and definition.closing:
            content = escape(first, quote=False)
            rendered = f"{definition.opening}{content}{definition.closing}"
            return tuple.__new__(type(self), (definition, rendered))
        arguments: tuple[Child | Mapping[str, Attribute], ...] = children
        if first is not _Missing.CHILD:
            arguments = (first, *children)
        attributes = definition.attributes
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
            return tuple.__new__(type(self), (definition, rendered))
        return type(self)._from_content(definition.name, attributes, content)

    def repeat(self, items: Iterable[Child], /) -> _Fragment:
        """Render one element per item, reusing attributes and replacing children."""
        definition = self[0]
        if not definition.closing:
            raise ValueError(f"The {definition.name} element cannot have children")
        opening, closing = definition.opening, definition.closing
        parts = []
        for item in items:
            content = escape(item, quote=False) if type(item) is str else _render_child(item)
            parts.extend((opening, content, closing))
        return _Fragment("".join(parts))

    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        """Encode rendered HTML for consumers such as FastAPI's HTMLResponse."""
        return str(self).encode(encoding, errors)

    def __str__(self) -> str:
        return self[1]

    def __reduce__(
        self,
    ) -> tuple[Callable[..., Self], tuple[str, tuple[tuple[str, Attribute], ...], str]]:
        definition = self[0]
        content = (
            self[1][len(definition.opening) : -len(definition.closing)]
            if definition.closing
            else ""
        )
        return type(self)._from_content, (definition.name, definition.attributes, content)
