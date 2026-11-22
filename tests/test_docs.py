"""Check the Markdown documentation build."""

import re
import shutil
import subprocess
import sys
from pathlib import Path


def test_build_docs(tmp_path: Path) -> None:
    """Build separate HTML pages with Markdown content and working link targets."""
    docs = Path(__file__).resolve().parents[1] / "docs"
    for name in ("build.py", "layout.py"):
        shutil.copy(docs / name, tmp_path / name)
    content = tmp_path / "content"
    content.mkdir()
    (content / "index.md").write_text("# Home\n\n[Elements](elements.html)\n", encoding="utf-8")
    (content / "elements.md").write_text(
        '# Elements\n\n```python\np("A < B & C")\n```\n', encoding="utf-8"
    )

    subprocess.run([sys.executable, str(tmp_path / "build.py")], check=True)

    home = (tmp_path / "index.html").read_text(encoding="utf-8")
    elements = (tmp_path / "elements.html").read_text(encoding="utf-8")
    assert home.startswith("<!doctype html>")
    for filename, page in (("index.html", home), ("elements.html", elements)):
        sidebar = page.split("<aside", 1)[1].split("</aside>", 1)[0]
        assert 'aria-label="Navigation"' in sidebar
        assert 'href="index.html"' in sidebar
        assert 'href="elements.html"' in sidebar
        current = re.findall(r'<a [^>]*aria-current="page"[^>]*>', sidebar)
        assert len(current) == 1
        assert f'href="{filename}"' in current[0]
    assert "<h1>Home</h1>" in home
    assert '<a href="elements.html">Elements</a>' in home
    assert "<h1>Elements</h1>" in elements
    assert '<pre><code class="language-python">' in elements
    assert "A &lt; B &amp; C" in elements
