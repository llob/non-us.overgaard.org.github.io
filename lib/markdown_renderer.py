"""
Markdown to HTML rendering functionality.

This module handles the conversion of Markdown content to HTML, including
parsing frontmatter metadata and rendering the content body.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime

import markdown


class MarkdownRenderer:
    """
    Converts Markdown text to HTML with frontmatter support.
    
    This class provides functionality to parse Markdown files that may contain
    YAML-style frontmatter and convert them to HTML. Uses the python-markdown
    library for Markdown rendering.
    
    Attributes:
        escape_html: Whether to escape HTML in the output (default: True).
    """
    
    def __init__(self, escape_html: bool = True) -> None:
        """
        Initialize the Markdown renderer.
        
        Args:
            escape_html: Whether to escape HTML entities in the output.
        """
        self.escape_html = escape_html
        self.markdown_instance = markdown.Markdown(
            escape_html=escape_html,
            extensions=[
                'extra',
                'codehilite',
            ]
        )
    
    def parse_frontmatter(self, markdown_text: str) -> Tuple[Dict[str, str], str]:
        """
        Parse YAML-style frontmatter from Markdown text.
        
        Args:
            markdown_text: The raw Markdown text potentially containing frontmatter.
            
        Returns:
            A tuple of (frontmatter_dict, content_without_frontmatter).
            
        Raises:
            ValueError: If frontmatter is malformed (missing closing delimiter).
        """
        if not markdown_text.startswith('---'):
            return {}, markdown_text
        
        end_index = markdown_text.find('\n---', 3)
        if end_index == -1:
            raise ValueError("Malformed frontmatter: missing closing '---'")
        
        frontmatter_content = markdown_text[3:end_index].strip()
        content = markdown_text[end_index + 4:].lstrip()
        
        frontmatter = {}
        for line in frontmatter_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                frontmatter[key] = value
        
        return frontmatter, content
    
    def parse_date(self, date_string: str) -> Optional[datetime]:
        """
        Parse a date string from frontmatter into a datetime object.
        
        Supports ISO format (YYYY-MM-DD) and extended formats.
        
        Args:
            date_string: The date string to parse.
            
        Returns:
            A datetime object, or None if parsing fails.
        """
        if not date_string:
            return None
        
        try:
            if len(date_string) == 10 and date_string.count('-') == 2:
                return datetime.strptime(date_string, "%Y-%m-%d")
            
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d",
                "%d %B %Y",
                "%B %d, %Y",
            ]:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            return datetime.strptime(date_string, "%Y-%m-%d")
            
        except (ValueError, TypeError):
            return None
    
    def render_markdown(self, markdown_text: str) -> str:
        """
        Convert Markdown text to HTML.
        
        Uses the python-markdown library for rendering. Supports all standard
        Markdown features including headers, paragraphs, bold and italic text,
        links, images, lists, blockquotes, code blocks, tables, and horizontal rules.
        
        Args:
            markdown_text: The Markdown text to convert.
            
        Returns:
            The converted HTML string.
        """
        self.markdown_instance.reset()
        html_content = self.markdown_instance.convert(markdown_text)
        return html_content
    
    def render_full_post(self, markdown_text: str) -> Tuple[Dict[str, str], str]:
        """
        Parse a complete Markdown post file and return frontmatter and rendered HTML.
        
        This is the main method for processing blog post files. It extracts
        frontmatter metadata and converts the Markdown content to HTML.
        
        Args:
            markdown_text: The complete Markdown text from a post file.
            
        Returns:
            A tuple of (frontmatter_dict, rendered_html).
            
        Raises:
            ValueError: If frontmatter is malformed.
        """
        frontmatter, content = self.parse_frontmatter(markdown_text)
        html_content = self.render_markdown(content)
        return frontmatter, html_content
