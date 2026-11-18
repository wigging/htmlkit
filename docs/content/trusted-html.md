# Trusted HTML

Use `Raw` for trusted markup that must not be escaped, such as scripts and styles:

```python
from htmlkit import Raw, head, script, style

head(
    style(Raw("body > main { margin: 0 auto }")),
    script(Raw("if (a < b && c) { go(); }")),
)
```

`Raw` is not sanitized. Child objects with an `__html__()` method also bypass escaping. The `Element`, `Fragment`, and `Raw` objects support this protocol for use with MarkupSafe, Jinja, and Django. Pass elements, fragments, and `Raw` directly as children. Converting them to `str` first causes their HTML to be escaped again.
