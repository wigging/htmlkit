"""Every conforming HTML element, grouped as in the HTML Living Standard.

Names follow the element index at https://html.spec.whatwg.org/multipage/indices.html.
Names that clash with Python keywords or built-ins have a trailing underscore:
``del_``, ``input_``, ``map_``, and ``object_``. The foreign ``svg`` and ``math``
elements are omitted.
"""

from .elements import Element

# The document element
html = Element("html")

# Document metadata
head = Element("head")
title = Element("title")
base = Element("base")
link = Element("link")
meta = Element("meta")
style = Element("style")

# Sections
body = Element("body")
article = Element("article")
section = Element("section")
nav = Element("nav")
aside = Element("aside")
h1 = Element("h1")
h2 = Element("h2")
h3 = Element("h3")
h4 = Element("h4")
h5 = Element("h5")
h6 = Element("h6")
hgroup = Element("hgroup")
header = Element("header")
footer = Element("footer")
address = Element("address")

# Grouping content
p = Element("p")
hr = Element("hr")
pre = Element("pre")
blockquote = Element("blockquote")
ol = Element("ol")
ul = Element("ul")
menu = Element("menu")
li = Element("li")
dl = Element("dl")
dt = Element("dt")
dd = Element("dd")
figure = Element("figure")
figcaption = Element("figcaption")
main = Element("main")
search = Element("search")
div = Element("div")

# Text-level semantics
a = Element("a")
em = Element("em")
strong = Element("strong")
small = Element("small")
s = Element("s")
cite = Element("cite")
q = Element("q")
dfn = Element("dfn")
abbr = Element("abbr")
ruby = Element("ruby")
rt = Element("rt")
rp = Element("rp")
data = Element("data")
time = Element("time")
code = Element("code")
var = Element("var")
samp = Element("samp")
kbd = Element("kbd")
sub = Element("sub")
sup = Element("sup")
i = Element("i")
b = Element("b")
u = Element("u")
mark = Element("mark")
bdi = Element("bdi")
bdo = Element("bdo")
span = Element("span")
br = Element("br")
wbr = Element("wbr")

# Edits
ins = Element("ins")
del_ = Element("del")

# Embedded content
picture = Element("picture")
source = Element("source")
img = Element("img")
iframe = Element("iframe")
embed = Element("embed")
object_ = Element("object")
video = Element("video")
audio = Element("audio")
track = Element("track")
map_ = Element("map")
area = Element("area")

# Tabular data
table = Element("table")
caption = Element("caption")
colgroup = Element("colgroup")
col = Element("col")
tbody = Element("tbody")
thead = Element("thead")
tfoot = Element("tfoot")
tr = Element("tr")
td = Element("td")
th = Element("th")

# Forms
form = Element("form")
label = Element("label")
input_ = Element("input")
button = Element("button")
select = Element("select")
option = Element("option")
optgroup = Element("optgroup")
selectedcontent = Element("selectedcontent")
datalist = Element("datalist")
textarea = Element("textarea")
output = Element("output")
progress = Element("progress")
meter = Element("meter")
fieldset = Element("fieldset")
legend = Element("legend")

# Interactive elements
details = Element("details")
summary = Element("summary")
dialog = Element("dialog")

# Scripting
script = Element("script")
noscript = Element("noscript")
template = Element("template")
slot = Element("slot")
canvas = Element("canvas")

__all__ = [
    "a",
    "abbr",
    "address",
    "area",
    "article",
    "aside",
    "audio",
    "b",
    "base",
    "bdi",
    "bdo",
    "blockquote",
    "body",
    "br",
    "button",
    "canvas",
    "caption",
    "cite",
    "code",
    "col",
    "colgroup",
    "data",
    "datalist",
    "dd",
    "del_",
    "details",
    "dfn",
    "dialog",
    "div",
    "dl",
    "dt",
    "em",
    "embed",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "header",
    "hgroup",
    "hr",
    "html",
    "i",
    "iframe",
    "img",
    "input_",
    "ins",
    "kbd",
    "label",
    "legend",
    "li",
    "link",
    "main",
    "map_",
    "mark",
    "menu",
    "meta",
    "meter",
    "nav",
    "noscript",
    "object_",
    "ol",
    "optgroup",
    "option",
    "output",
    "p",
    "picture",
    "pre",
    "progress",
    "q",
    "rp",
    "rt",
    "ruby",
    "s",
    "samp",
    "script",
    "search",
    "section",
    "select",
    "selectedcontent",
    "slot",
    "small",
    "source",
    "span",
    "strong",
    "style",
    "sub",
    "summary",
    "sup",
    "table",
    "tbody",
    "td",
    "template",
    "textarea",
    "tfoot",
    "th",
    "thead",
    "time",
    "title",
    "tr",
    "track",
    "u",
    "ul",
    "var",
    "video",
    "wbr",
]
