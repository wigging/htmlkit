"""Build HTML documents with Python objects."""

from . import tags
from .elements import Attribute, Child, Element, Fragment, Raw, SupportsHtml
from .tags import *

__all__ = ["Attribute", "Child", "Element", "Fragment", "Raw", "SupportsHtml"] + tags.__all__
