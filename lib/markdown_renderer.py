"""
Markdown to HTML rendering functionality.

This module handles the conversion of Markdown content to HTML, including
parsing frontmatter metadata and rendering the content body.
"""

import html
import re
from typing import Dict, Optional, Tuple
from datetime import datetime


class MarkdownRenderer:
    """
    Converts Markdown text to HTML with frontmatter support.
    
    This class provides functionality to parse Markdown files that may contain
    YAML-style frontmatter and convert them to HTML. The implementation uses
    a simple, dependency-free approach for basic Markdown rendering.
    
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
        # Check if the text starts with frontmatter
        if not markdown_text.startswith('---'):
            return {}, markdown_text
        
        # Find the closing frontmatter delimiter
        end_index = markdown_text.find('\n---', 3)
        if end_index == -1:
            raise ValueError("Malformed frontmatter: missing closing '---'")
        
        # Extract frontmatter content
        frontmatter_content = markdown_text[3:end_index].strip()
        content = markdown_text[end_index + 4:].lstrip()
        
        # Parse simple YAML-style key-value pairs
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
            # Try ISO format first (YYYY-MM-DD)
            if len(date_string) == 10 and date_string.count('-') == 2:
                return datetime.strptime(date_string, "%Y-%m-%d")
            
            # Try other common formats
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
            
            # If none of the above worked, try date-only parsing
            return datetime.strptime(date_string, "%Y-%m-%d")
            
        except (ValueError, TypeError):
            return None
    
    def render_markdown(self, markdown_text: str) -> str:
        """
        Convert Markdown text to HTML.
        
        This is a basic Markdown renderer that handles the most common elements:
        - Headers (#, ##, ###)
        - Paragraphs
        - Bold and italic text
        - Links
        - Images
        - Unordered and ordered lists
        - Blockquotes
        - Code blocks (inline and block)
        - Horizontal rules
        
        Args:
            markdown_text: The Markdown text to convert.
            
        Returns:
            The converted HTML string.
        """
        # Split into lines and process each line
        lines = markdown_text.split('\n')
        html_lines = []
        in_list = False
        in_blockquote = False
        in_code_block = False
        code_block_language = ""
        
        for line in lines:
            stripped = line.strip()
            
            # Handle code blocks (```)
            if stripped.startswith('```'):
                if in_code_block:
                    # End code block
                    html_lines.append('</code></pre>')
                    in_code_block = False
                    code_block_language = ""
                else:
                    # Start code block
                    language = stripped[3:].strip()
                    html_lines.append(f'<pre><code class="language-{language}">')
                    in_code_block = True
                    code_block_language = language
                continue
            
            if in_code_block:
                # Escape HTML in code blocks
                escaped_line = html.escape(line)
                html_lines.append(escaped_line)
                continue
            
            # Handle blockquotes
            if stripped.startswith('>'):
                if not in_blockquote:
                    html_lines.append('<blockquote>')
                    in_blockquote = True
                # Remove the > and any following space
                content = stripped[1:].lstrip()
                html_lines.append(f'<p>{self._render_inline_markdown(content)}</p>')
                continue
            else:
                if in_blockquote:
                    html_lines.append('</blockquote>')
                    in_blockquote = False
            
            # Handle headers
            if stripped.startswith('#'):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                
                header_level = 0
                while header_level < len(stripped) and stripped[header_level] == '#':
                    header_level += 1
                
                if header_level > 6:
                    header_level = 6
                    
                header_text = stripped[header_level:].lstrip()
                html_lines.append(f'<h{header_level}>{self._render_inline_markdown(header_text)}</h{header_level}>')
                continue
            
            # Handle horizontal rules
            if stripped in ('---', '***', '___'):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('<hr>')
                continue
            
            # Handle unordered list items
            if stripped.startswith(('- ', '* ', '+ ')):
                if not in_list:
                    if html_lines and html_lines[-1] != '</ul>':
                        # Close any open paragraph
                        if html_lines and '<p>' in html_lines[-1]:
                            html_lines.append('</p>')
                    html_lines.append('<ul>')
                    in_list = True
                
                # Extract list item content (remove the bullet and space)
                list_content = stripped[2:].lstrip()
                html_lines.append(f'<li>{self._render_inline_markdown(list_content)}</li>')
                continue
            
            # Handle ordered list items
            list_match = re.match(r'^(\d+)\.\s+(.*)', stripped)
            if list_match:
                if not in_list:
                    if html_lines and html_lines[-1] != '</ol>':
                        # Close any open paragraph
                        if html_lines and '<p>' in html_lines[-1]:
                            html_lines.append('</p>')
                    html_lines.append('<ol>')
                    in_list = True
                
                list_content = list_match.group(2)
                html_lines.append(f'<li>{self._render_inline_markdown(list_content)}</li>')
                continue
            
            # Handle regular paragraphs
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            
            if stripped:  # Only process non-empty lines
                if not (html_lines and html_lines[-1].startswith('<p>')):
                    html_lines.append('<p>')
                else:
                    html_lines.append('<br>')
                
                html_lines.append(self._render_inline_markdown(stripped))
            else:
                # Empty line - close open paragraph if needed
                if html_lines and html_lines[-1].startswith('<p>'):
                    html_lines.append('</p>')
        
        # Close any open blocks
        if in_list:
            html_lines.append('</ul>')
        if in_blockquote:
            html_lines.append('</blockquote>')
        if in_code_block:
            html_lines.append('</code></pre>')
        
        # Close any open paragraph
        if html_lines and html_lines[-1].startswith('<p>'):
            html_lines.append('</p>')
        
        return '\n'.join(html_lines)
    
    def _render_inline_markdown(self, text: str) -> str:
        """
        Render inline Markdown elements (bold, italic, links, etc.).
        
        Args:
            text: The text containing inline Markdown.
            
        Returns:
            The text with inline Markdown converted to HTML.
        """
        if not text:
            return ""
        
        # Escape HTML first to prevent XSS
        if self.escape_html:
            text = html.escape(text)
        
        # Handle images: ![alt](url)
        text = re.sub(
            r'!\[([^\]]*)\]\(([^\)]+)\)',
            r'<img src="\2" alt="\1">',
            text
        )
        
        # Handle links: [text](url)
        text = re.sub(
            r'\[([^\]]+)\]\(([^\)]+)\)',
            r'<a href="\2">\1</a>',
            text
        )
        
        # Handle inline code: `code`
        text = re.sub(
            r'`([^`]+)`',
            r'<code>\1</code>',
            text
        )
        
        # Handle bold: **text** or __text__
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)
        
        # Handle italic: *text* or _text_
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
        
        # Handle strikethrough: ~~text~~
        text = re.sub(r'~~([^~]+)~~', r'<del>\1</del>', text)
        
        return text
    
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