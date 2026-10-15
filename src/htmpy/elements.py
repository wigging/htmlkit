"""HTML element construction, attribute validation, and rendering."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from html import escape

type Child = str | int | Element | None | list[Child] | tuple[Child, ...]
type Attribute = str | int | bool | None


def _render_child(child: Child) -> str:
    if child is None:
        return ""
    if isinstance(child, Element):
        return str(child)
    if isinstance(child, (str, int)):
        return escape(str(child), quote=False)
    if isinstance(child, (list, tuple)):
        return "".join(_render_child(item) for item in child)
    raise TypeError(f"Unsupported HTML child: {type(child).__name__}")


@dataclass(frozen=True)
class Element:
    """An immutable HTML element with an optional attribute dictionary first."""

    _tag: str
    _attributes: tuple[tuple[str, Attribute], ...] = ()
    _content: str = ""

    def __call__(self, *children: Child | Mapping[str, Attribute]) -> Element:
        """Set children, optionally merging attributes from a leading dictionary."""
        attributes = children[0] if children and isinstance(children[0], Mapping) else {}
        content = children[1:] if children and isinstance(children[0], Mapping) else children
        merged = dict(self._attributes)
        for name, value in attributes.items():
            if not re.fullmatch(r"[A-Za-z_:][A-Za-z0-9_.:-]*", name):
                raise ValueError(f"Invalid HTML attribute name: {name!r}")
            if value is not None and not isinstance(value, (str, int, bool)):
                raise TypeError(f"Unsupported HTML attribute value: {type(value).__name__}")
            merged[name] = value
        rendered = []
        for child in content:
            if isinstance(child, Mapping):
                raise TypeError("Attributes must be the first argument, not a child")
            rendered.append(_render_child(child))
        return replace(self, _attributes=tuple(merged.items()), _content="".join(rendered))

    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        """Encode rendered HTML for consumers such as FastAPI's HTMLResponse."""
        return str(self).encode(encoding, errors)

    def __str__(self) -> str:
        attributes = []
        for name, value in self._attributes:
            if value is None or value is False:
                continue
            if value is True:
                attributes.append(f" {name}")
            else:
                attributes.append(f' {name}="{escape(str(value), quote=True)}"')
        doctype = "<!doctype html>" if self._tag == "html" else ""
        return f"{doctype}<{self._tag}{''.join(attributes)}>{self._content}</{self._tag}>"
