"""
Site generator for the static blog system.

This module provides the main SiteGenerator class that orchestrates the entire
static site generation process, including loading posts, rendering templates,
and writing output files.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .models import Post, SiteConfig, Pagination
from .markdown_renderer import MarkdownRenderer
from .template_engine import TemplateEngine


# Configure logging
logger = logging.getLogger(__name__)


class SiteGenerator:
    """
    Main class for generating the static blog site.
    
    This class coordinates the entire build process:
    1. Loading and parsing Markdown post files
    2. Sorting posts by date
    3. Rendering templates with post data
    4. Writing HTML output files
    5. Creating pagination for post archives
    
    Attributes:
        config: Site configuration.
        markdown_renderer: Markdown to HTML converter.
        template_engine: Template rendering engine.
        posts: List of loaded posts.
    """
    
    def __init__(self, config: Optional[SiteConfig] = None) -> None:
        """
        Initialize the site generator.
        
        Args:
            config: Site configuration. Uses default values if None.
        """
        self.config = config or SiteConfig()
        self.markdown_renderer = MarkdownRenderer(escape_html=True)
        self.template_engine = TemplateEngine(template_dir=self.config.template_dir)
        self.posts: List[Post] = []
        self._post_cache: Dict[str, Post] = {}  # Cache posts by slug
    
    def load_posts(self) -> List[Post]:
        """
        Load all post files from the content directory.
        
        Scans the content directory for Markdown files (*.md), parses each
        file for frontmatter and content, and creates Post objects.
        
        Returns:
            List of Post objects sorted by date (newest first).
            
        Raises:
            FileNotFoundError: If the content directory doesn't exist.
        """
        content_dir = Path(self.config.content_dir)
        
        if not content_dir.exists():
            logger.warning(f"Content directory not found: {content_dir}")
            return []
        
        # Clear existing cache
        self._post_cache.clear()
        self.posts = []
        
        # Find all markdown files
        markdown_files = list(content_dir.glob('**/*.md'))
        
        if not markdown_files:
            logger.warning(f"No Markdown files found in {content_dir}")
            return []
        
        loaded_posts = []
        
        for file_path in markdown_files:
            try:
                post = self._load_single_post(file_path)
                if post:
                    loaded_posts.append(post)
                    self._post_cache[post.slug] = post
            except Exception as e:
                logger.error(f"Error loading post from {file_path}: {e}")
                continue
        
        # Sort posts by date (newest first)
        loaded_posts.sort(key=lambda p: p.date, reverse=True)
        self.posts = loaded_posts
        
        logger.info(f"Loaded {len(self.posts)} posts from {content_dir}")
        return self.posts
    
    def _load_single_post(self, file_path: Path) -> Optional[Post]:
        """
        Load a single post from a Markdown file.
        
        Args:
            file_path: Path to the Markdown file.
            
        Returns:
            A Post object, or None if the file couldn't be parsed.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
        except (IOError, UnicodeDecodeError) as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
        
        # Parse frontmatter and content
        try:
            frontmatter, html_content = self.markdown_renderer.render_full_post(markdown_content)
        except ValueError as e:
            logger.error(f"Error parsing frontmatter in {file_path}: {e}")
            return None
        
        # Extract metadata from frontmatter
        title = frontmatter.get('title', '')
        if not title:
            # Try to extract title from filename if not in frontmatter
            title = file_path.stem.replace('-', ' ').title()
        
        slug = frontmatter.get('slug', '')
        if not slug:
            # Auto-generate slug from title
            slug = Post._generate_slug(title)
        
        # Parse date
        date_string = frontmatter.get('date', '')
        date = self.markdown_renderer.parse_date(date_string)
        if not date:
            # Use file modification time as fallback
            date = datetime.fromtimestamp(file_path.stat().st_mtime)
            logger.warning(f"No valid date found in {file_path}, using file modification time")
        
        description = frontmatter.get('description', '')
        
        try:
            post = Post(
                title=title,
                slug=slug,
                date=date,
                description=description,
                content=markdown_content,
                html_content=html_content,
                raw_frontmatter=frontmatter
            )
            return post
        except ValueError as e:
            logger.error(f"Error creating Post object from {file_path}: {e}")
            return None
    
    def generate_site(self) -> None:
        """
        Generate the complete static site.
        
        This is the main method that orchestrates the entire build process:
        1. Load all posts
        2. Create output directory structure
        3. Generate index page with latest posts
        4. Generate individual post pages
        5. Generate pagination/archive pages
        6. Copy static assets (CSS, etc.)
        """
        logger.info("Starting site generation...")
        
        # Load posts
        self.load_posts()
        
        # Create output directory structure
        self._create_output_directory()
        
        # Generate index page (front page with latest posts)
        self._generate_index_page()
        
        # Generate individual post pages
        self._generate_post_pages()
        
        # Generate pagination/archive pages
        self._generate_pagination_pages()
        
        # Generate archive page (all posts)
        self._generate_archive_page()
        
        # Copy static assets
        self._copy_assets()
        
        # Copy media files
        self._copy_media_files(
            Path(self.config.content_dir).parent,
            Path(self.config.output_dir)
        )
        
        logger.info("Site generation completed!")
    
    def _create_output_directory(self) -> None:
        """Create the output directory structure."""
        output_dir = Path(self.config.output_dir)
        
        # Create main directories
        dirs_to_create = [
            output_dir,
            output_dir / "posts",
            output_dir / "page",
            output_dir / "assets",
        ]
        
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created output directory structure in {output_dir}")
    
    def _generate_index_page(self) -> None:
        """Generate the front page with the latest posts."""
        output_path = Path(self.config.output_dir) / "index.html"
        
        # Get the latest posts (first page)
        latest_posts = self.posts[:self.config.posts_per_page]
        
        # Check if there are more posts
        has_more_posts = len(self.posts) > self.config.posts_per_page
        
        context = {
            "site_title": self.config.title,
            "site_description": self.config.description,
            "base_url": self.config.base_url,
            "relative_prefix": "",
            "posts": [self._post_to_template_dict(post) for post in latest_posts],
            "has_more_posts": has_more_posts,
            "next_page_url": "page/2/" if has_more_posts else None,
            "is_index": True,
            "current_page": 1,
            "total_pages": max(1, (len(self.posts) + self.config.posts_per_page - 1) // self.config.posts_per_page),
        }
        
        try:
            html_content = self.template_engine.render("index.html", context)
            self._write_output_file(output_path, html_content)
            logger.info(f"Generated index page: {output_path}")
        except Exception as e:
            logger.error(f"Error generating index page: {e}")
    
    def _generate_post_pages(self) -> None:
        """Generate individual pages for each post."""
        if not self.posts:
            logger.info("No posts to generate individual pages for")
            return
        
        posts_dir = Path(self.config.output_dir) / "posts"
        content_dir = Path(self.config.content_dir)
        
        for post in self.posts:
            # Create directory for this post
            post_dir = posts_dir / post.slug
            post_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate the post page
            output_path = post_dir / "index.html"
            
            # Get the flattened post dictionary
            post_dict = self._post_to_template_dict(post)
            
            # Merge the post fields directly into the context for simpler template access
            context = {
                "site_title": self.config.title,
                "site_description": self.config.description,
                "base_url": self.config.base_url,
                "relative_prefix": "../../",
                "is_post": True,
            }
            # Add all post fields directly to the context
            context.update(post_dict)
            # Also keep the post object for compatibility
            context["post"] = post_dict
            context["current_post"] = post_dict
            
            try:
                html_content = self.template_engine.render("post.html", context)
                self._write_output_file(output_path, html_content)
                logger.info(f"Generated post page: {output_path}")
            except Exception as e:
                logger.error(f"Error generating post page for {post.slug}: {e}")
        
        # Copy media files from content directory to output directory
        self._copy_media_files(content_dir, posts_dir)
    
    def _generate_pagination_pages(self) -> None:
        """Generate pagination pages for post archives."""
        total_posts = len(self.posts)
        posts_per_page = self.config.posts_per_page
        total_pages = max(1, (total_posts + posts_per_page - 1) // posts_per_page)
        
        if total_pages <= 1:
            # No pagination needed
            return
        
        page_dir = Path(self.config.output_dir) / "page"
        
        for page_num in range(2, total_pages + 1):
            # Calculate posts for this page
            start_idx = (page_num - 1) * posts_per_page
            end_idx = min(start_idx + posts_per_page, total_posts)
            page_posts = self.posts[start_idx:end_idx]
            
            # Create directory for this page
            page_output_dir = page_dir / str(page_num)
            page_output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = page_output_dir / "index.html"
            
            pagination = Pagination(
                current_page=page_num,
                total_pages=total_pages,
                posts=page_posts,
                base_url=self.config.base_url
            )
            
            # Flatten pagination object for template compatibility
            pagination_dict = {
                "current_page": pagination.current_page,
                "total_pages": pagination.total_pages,
                "has_previous": pagination.has_previous,
                "has_next": pagination.has_next,
                "previous_page_url": pagination.previous_page_url,
                "next_page_url": pagination.next_page_url,
            }
            
            context = {
                "site_title": self.config.title,
                "site_description": self.config.description,
                "base_url": self.config.base_url,
                "relative_prefix": "../../",
                "posts": [self._post_to_template_dict(post) for post in page_posts],
                "pagination": pagination_dict,  # Keep for compatibility
                "current_page": page_num,
                "total_pages": total_pages,
                "is_archive": True,
            }
            # Also add all pagination fields directly
            context.update(pagination_dict)
            
            try:
                html_content = self.template_engine.render("archive.html", context)
                self._write_output_file(output_path, html_content)
                logger.info(f"Generated pagination page: {output_path}")
            except Exception as e:
                logger.error(f"Error generating pagination page {page_num}: {e}")
    
    def _generate_archive_page(self) -> None:
        """Generate an archive page with all posts."""
        output_path = Path(self.config.output_dir) / "archive.html"
        
        # Calculate pagination info for archive (single page showing all posts)
        total_pages = self.get_total_pages()
        
        context = {
            "site_title": self.config.title,
            "site_description": self.config.description,
            "base_url": self.config.base_url,
            "relative_prefix": "",
            "posts": [self._post_to_template_dict(post) for post in self.posts],
            "is_archive": True,
            "archive_title": "All Posts Archive",
            "current_page": 1,
            "total_pages": total_pages,
            "has_previous": False,
            "has_next": total_pages > 1,
            "previous_page_url": None,
            "next_page_url": "page/2/" if total_pages > 1 else None,
        }
        
        try:
            html_content = self.template_engine.render("archive.html", context)
            self._write_output_file(output_path, html_content)
            logger.info(f"Generated archive page: {output_path}")
        except Exception as e:
            logger.error(f"Error generating archive page: {e}")
    
    def _copy_assets(self) -> None:
        """Copy static assets (CSS, etc.) to the output directory."""
        assets_src = Path(self.config.template_dir) / "assets"
        assets_dest = Path(self.config.output_dir) / "assets"
        
        if not assets_src.exists():
            logger.info("No assets directory found in templates")
            return
        
        # Ensure destination directory exists
        assets_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy all files from source to destination
        for file_path in assets_src.glob('*'):
            if file_path.is_file():
                dest_path = assets_dest / file_path.name
                try:
                    shutil.copy2(file_path, dest_path)
                    logger.info(f"Copied asset: {file_path} -> {dest_path}")
                except IOError as e:
                    logger.error(f"Error copying asset {file_path}: {e}")
        
        # Also copy favicon.ico to the root of the output directory for GitHub Pages
        favicon_src = assets_src / "favicon.ico"
        favicon_dest = Path(self.config.output_dir) / "favicon.ico"
        if favicon_src.exists():
            try:
                shutil.copy2(favicon_src, favicon_dest)
                logger.info(f"Copied favicon to root: {favicon_src} -> {favicon_dest}")
            except IOError as e:
                logger.error(f"Error copying favicon to root: {e}")
    
    def _copy_media_files(self, content_dir: Path, output_root: Path) -> None:
        """Copy media files from content directory to output directory.
        
        Copies all non-markdown files from content/posts/ to docs/posts/,
        preserving the directory structure. Media files can be referenced in
        Markdown using paths relative to the posts directory.
        
        Args:
            content_dir: Source directory containing content and media files.
            output_root: Root output directory (docs/).
        """
        if not content_dir.exists():
            return
        
        # Copy all files from content/posts/ to docs/posts/, excluding markdown files
        posts_content_dir = content_dir / "posts"
        posts_output_dir = output_root / "posts"
        
        if posts_content_dir.exists():
            posts_output_dir.mkdir(parents=True, exist_ok=True)
            
            for item in posts_content_dir.rglob('*'):
                if item.is_file() and item.suffix.lower() != '.md':
                    # Calculate relative path from posts_content_dir
                    relative_path = item.relative_to(posts_content_dir)
                    output_path = posts_output_dir / relative_path
                    
                    try:
                        # Ensure destination directory exists
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, output_path)
                        logger.info(f"Copied media file: {item} -> {output_path}")
                    except IOError as e:
                        logger.error(f"Error copying media file {item}: {e}")
    
    def _write_output_file(self, output_path: Path, content: str) -> None:
        """
        Write content to an output file.
        
        Args:
            output_path: Path to the output file.
            content: HTML content to write.
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except IOError as e:
            raise IOError(f"Error writing to {output_path}: {e}")
    
    def get_post_by_slug(self, slug: str) -> Optional[Post]:
        """
        Get a post by its slug.
        
        Args:
            slug: The post slug.
            
        Returns:
            The Post object, or None if not found.
        """
        return self._post_cache.get(slug)
    
    def get_total_posts(self) -> int:
        """Return the total number of posts."""
        return len(self.posts)
    
    def get_total_pages(self) -> int:
        """Return the total number of pagination pages."""
        if not self.posts:
            return 1
        return max(1, (len(self.posts) + self.config.posts_per_page - 1) // self.config.posts_per_page)
    
    def _post_to_template_dict(self, post: Post) -> Dict[str, Any]:
        """
        Convert a Post object to a dictionary suitable for templates.
        
        This flattens the Post object to avoid dot notation in templates.
        
        Args:
            post: The Post object to convert.
            
        Returns:
            A dictionary with flattened post data.
        """
        return {
            "title": post.title,
            "slug": post.slug,
            "date": post.date,
            "description": post.description or "",
            "content": post.content,
            "html_content": post.html_content,
            "formatted_date": post.formatted_date,
            "iso_date": post.iso_date,
            "url": post.url,
        }
    
    def clean_output_dir(self) -> None:
        """
        Clean the output directory by removing all generated files.
        
        This is useful for a clean rebuild.
        """
        output_dir = Path(self.config.output_dir)
        
        if not output_dir.exists():
            return
        
        # Remove all files and directories except .git (if it exists)
        for item in output_dir.iterdir():
            if item.name == '.git':
                continue
            if item.is_file():
                try:
                    item.unlink()
                except IOError as e:
                    logger.error(f"Error removing file {item}: {e}")
            elif item.is_dir():
                try:
                    shutil.rmtree(item)
                except IOError as e:
                    logger.error(f"Error removing directory {item}: {e}")
        
        logger.info(f"Cleaned output directory: {output_dir}")