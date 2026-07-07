"""
Static blog generator library package.

This package contains the core functionality for generating a static blog site
from Markdown content files and HTML templates.
"""

from .models import Post, SiteConfig, Pagination
from .markdown_renderer import MarkdownRenderer
from .template_engine import TemplateEngine
from .generator import SiteGenerator

__all__ = [
    "Post",
    "SiteConfig", 
    "Pagination",
    "MarkdownRenderer",
    "TemplateEngine",
    "SiteGenerator",
]

__version__ = "1.0.0"