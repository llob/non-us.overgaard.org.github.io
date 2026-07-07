"""
Data models for the static blog generator.

This module defines the core data structures used throughout the blog generation
process, including Post, SiteConfig, and Pagination models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import re


@dataclass
class Post:
    """
    Represents a blog post with metadata and content.
    
    Attributes:
        title: The title of the post.
        slug: URL-friendly identifier for the post.
        date: Publication date of the post.
        description: Optional short description/excerpt.
        content: The main content of the post (Markdown format).
        html_content: The rendered HTML content (generated from Markdown).
        raw_frontmatter: The original frontmatter as a dictionary.
    """
    title: str
    slug: str
    date: datetime
    description: Optional[str] = None
    content: str = ""
    html_content: str = ""
    raw_frontmatter: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate post data after initialization."""
        if not self.title:
            raise ValueError("Post title cannot be empty")
        if not self.slug:
            # Auto-generate slug from title if not provided
            self.slug = self._generate_slug(self.title)
        if not isinstance(self.date, datetime):
            raise ValueError("Post date must be a datetime object")
    
    @staticmethod
    def _generate_slug(title: str) -> str:
        """
        Generate a URL-friendly slug from a title.
        
        Args:
            title: The title to convert to a slug.
            
        Returns:
            A URL-friendly slug string.
        """
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower().strip()
        # Remove special characters and replace spaces
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')
    
    @property
    def url(self) -> str:
        """Generate the URL path for this post."""
        return f"/posts/{self.slug}/"
    
    @property
    def formatted_date(self) -> str:
        """Return the date formatted for display."""
        return self.date.strftime("%B %d, %Y")
    
    @property
    def iso_date(self) -> str:
        """Return the date in ISO format."""
        return self.date.isoformat()


@dataclass
class SiteConfig:
    """
    Configuration for the blog site.
    
    Attributes:
        title: The title of the blog.
        description: Short description of the blog.
        author: Author name.
        base_url: Base URL for the site.
        posts_per_page: Number of posts to show on each page.
        template_dir: Directory containing HTML templates.
        content_dir: Directory containing Markdown content files.
        output_dir: Directory where generated HTML files will be saved.
    """
    title: str = "Going cold turkey on the US"
    description: str = "A journey towards a sovereign tech stack"
    author: str = ""
    base_url: str = "/"
    posts_per_page: int = 5
    template_dir: str = "templates"
    content_dir: str = "content/posts"
    output_dir: str = "docs"
    
    def __post_init__(self) -> None:
        """Validate site configuration after initialization."""
        if not self.title:
            raise ValueError("Site title cannot be empty")
        if self.posts_per_page < 1:
            raise ValueError("posts_per_page must be at least 1")


@dataclass
class Pagination:
    """
    Pagination information for listing posts across multiple pages.
    
    Attributes:
        current_page: The current page number (1-indexed).
        total_pages: Total number of pages available.
        posts: List of posts for the current page.
        has_previous: Whether there is a previous page.
        has_next: Whether there is a next page.
        previous_page_url: URL to the previous page, or None.
        next_page_url: URL to the next page, or None.
    """
    current_page: int
    total_pages: int
    posts: List[Post]
    base_url: str = "/"
    
    def __post_init__(self) -> None:
        """Calculate pagination properties after initialization."""
        self.has_previous = self.current_page > 1
        self.has_next = self.current_page < self.total_pages
        self.previous_page_url = self._generate_page_url(self.current_page - 1) if self.has_previous else None
        self.next_page_url = self._generate_page_url(self.current_page + 1) if self.has_next else None
    
    def _generate_page_url(self, page_num: int) -> str:
        """Generate URL for a specific page number."""
        if page_num == 1:
            return self.base_url
        return f"{self.base_url}page/{page_num}/"
    
    @property
    def page_range(self) -> List[int]:
        """Generate a range of page numbers for navigation."""
        if self.total_pages <= 7:
            return list(range(1, self.total_pages + 1))
        
        # For more pages, show current page with 2 pages on each side
        start = max(2, self.current_page - 2)
        end = min(self.total_pages - 1, self.current_page + 2)
        
        pages = []
        # Always include first page
        pages.append(1)
        
        # Add ellipsis if there's a gap
        if start > 2:
            pages.append(-1)  # Use -1 to represent ellipsis
        
        # Add pages around current page
        pages.extend(range(start, end + 1))
        
        # Add ellipsis if there's a gap
        if end < self.total_pages - 1:
            pages.append(-1)
        
        # Always include last page
        if self.total_pages > 1:
            pages.append(self.total_pages)
        
        return pages