"""HTML element construction, attribute validation, and rendering."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from html import escape

type Child = str | int | Element | None | list[Child] | tuple[Child, ...]
type Attribute = str | int | bool | None

_ATTRIBUTE_NAME = re.compile(r"[A-Za-z_:][A-Za-z0-9_.:-]*")


@lru_cache(maxsize=256)
def _valid_attribute_name(name: str) -> bool:
    return _ATTRIBUTE_NAME.fullmatch(name) is not None


def _render_child(child: Child | Mapping[str, Attribute]) -> str:
    if type(child) is str:
        return escape(child, quote=False)
    if child is None:
        return ""
    if isinstance(child, Element):
        return str(child)
    if isinstance(child, (str, int)):
        return escape(str(child), quote=False)
    if isinstance(child, (list, tuple)):
        return "".join(_render_child(item) for item in child)
    if isinstance(child, Mapping):
        raise TypeError("Attributes must be the first argument, not a child")
    raise TypeError(f"Unsupported HTML child: {type(child).__name__}")


@dataclass(frozen=True, slots=True)
class Element:
    """An immutable HTML element with an optional attribute dictionary first."""

    _tag: str
    _attributes: tuple[tuple[str, Attribute], ...] = ()
    _content: str = ""

    def __call__(self, *children: Child | Mapping[str, Attribute]) -> Element:
        """Set children, optionally merging attributes from a leading dictionary."""
        attributes = self._attributes
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
        if not children:
            content = ""
        elif len(children) == 1:
            content = _render_child(children[0])
        else:
            content = "".join([_render_child(child) for child in children])
        return type(self)(self._tag, attributes, content)

    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        """Encode rendered HTML for consumers such as FastAPI's HTMLResponse."""
        return str(self).encode(encoding, errors)

    def __str__(self) -> str:
        doctype = "<!doctype html>" if self._tag == "html" else ""
        if not self._attributes:
            return f"{doctype}<{self._tag}>{self._content}</{self._tag}>"
        attributes = []
        for name, value in self._attributes:
            if value is None or value is False:
                continue
            if value is True:
                attributes.append(f" {name}")
            else:
                attributes.append(f' {name}="{escape(str(value), quote=True)}"')
        return f"{doctype}<{self._tag}{''.join(attributes)}>{self._content}</{self._tag}>"
