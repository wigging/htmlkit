"""HTML element construction, attribute validation, and rendering."""

import re
from collections.abc import Iterable, Mapping
from enum import Enum
from functools import lru_cache
from html import escape
from typing import NamedTuple, Self

type Child = str | int | Element | _Fragment | None | list[Child] | tuple[Child, ...]
type Attribute = str | int | bool | None

_ATTRIBUTE_NAME = re.compile(r"[A-Za-z_:][A-Za-z0-9_.:-]*")
_VOID_TAGS = frozenset({"meta", "link"})


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
    """An immutable HTML element with an optional attribute dictionary first."""

    # Share the tag definition between calls; store fully rendered HTML per element.
    __slots__ = ()

    def __new__(
        cls,
        _tag: str,
        _attributes: tuple[tuple[str, Attribute], ...] = (),
        _content: str = "",
    ) -> Self:
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

    def __call__(
        self,
        first: Child | Mapping[str, Attribute] | _Missing = _Missing.CHILD,
        /,
        *children: Child | Mapping[str, Attribute],
    ) -> Element:
        """Set children, optionally merging attributes from a leading dictionary."""
        definition = self[0]
        if type(first) is str and not children and definition.closing:
            content = escape(first, quote=False)
            rendered = f"{definition.opening}{content}{definition.closing}"
            return tuple.__new__(type(self), (definition, rendered))
        if first is not _Missing.CHILD:
            children = (first, *children)
        attributes = definition.attributes
        if children and (
            isinstance(children[0], dict)
            or (type(children[0]) not in (str, Element) and isinstance(children[0], Mapping))
        ):
            updates = tuple(children[0].items())
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
            children = children[1:]
        if not definition.closing and children:
            raise ValueError(f"The {definition.name} element cannot have children")
        if not children:
            content = ""
        elif len(children) == 1:
            content = _render_child(children[0])
        else:
            content = "".join([_render_child(child) for child in children])
        if attributes is definition.attributes:
            rendered = (
                f"{definition.opening}{content}{definition.closing}"
                if definition.closing
                else definition.opening
            )
            return tuple.__new__(type(self), (definition, rendered))
        return type(self)(definition.name, attributes, content)

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

    def __getnewargs__(self) -> tuple[str, tuple[tuple[str, Attribute], ...], str]:
        definition = self[0]
        content = (
            self[1][len(definition.opening) : -len(definition.closing)]
            if definition.closing
            else ""
        )
        return definition.name, definition.attributes, content
