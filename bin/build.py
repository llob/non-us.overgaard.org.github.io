#!/usr/bin/env python3
"""
Build script for the static blog generator.

This script is the main entry point for generating the static blog site.
It can be run from the command line to build the entire site or perform
specific tasks like cleaning the output directory.

Usage:
    python bin/build.py          # Build the site
    python bin/build.py --clean  # Clean the output directory first
    python bin/build.py --debug  # Show debug output
    python bin/build.py --help   # Show this help message
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the lib directory to Python path so we can import our modules
script_dir = Path(__file__).parent
repo_root = script_dir.parent
lib_dir = repo_root / "lib"

if str(lib_dir) not in sys.path:
    sys.path.insert(0, str(lib_dir))

# Also add the parent directory to path to allow relative imports
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.generator import SiteGenerator
from lib.models import SiteConfig


def setup_logging(debug: bool = False) -> None:
    """
    Configure logging for the build process.
    
    Args:
        debug: If True, set logging level to DEBUG for verbose output.
    """
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_default_config() -> SiteConfig:
    """
    Get the default site configuration.
    
    Returns:
        A SiteConfig object with default values.
    """
    return SiteConfig(
        title="Going cold turkey on the US",
        description="A journey towards a sovereign tech stack",
        author="",
        base_url="",
        posts_per_page=5,
        template_dir=str(Path(__file__).parent.parent / "templates"),
        content_dir=str(Path(__file__).parent.parent / "content" / "posts"),
        output_dir=str(Path(__file__).parent.parent / "docs")
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        The parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Static Blog Generator - Build your blog site from Markdown content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s                   # Build the site
    %(prog)s --clean           # Clean output directory and rebuild
    %(prog)s --debug           # Show debug output
    %(prog)s --title "My Blog" # Override site title
        """
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean the output directory before building"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug output during build"
    )
    
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Override the site title"
    )
    
    parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="Override the site description"
    )
    
    parser.add_argument(
        "--author",
        type=str,
        default=None,
        help="Override the author name"
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Override the base URL for the site"
    )
    
    parser.add_argument(
        "--posts-per-page",
        type=int,
        default=None,
        help="Override the number of posts per page"
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main function for the build script.
    
    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Set up logging
        setup_logging(debug=args.debug)
        
        # Get default configuration
        config = get_default_config()
        
        # Override configuration with command line arguments
        if args.title:
            config.title = args.title
        if args.description:
            config.description = args.description
        if args.author:
            config.author = args.author
        if args.base_url:
            config.base_url = args.base_url
        if args.posts_per_page:
            config.posts_per_page = args.posts_per_page
        
        # Create site generator
        generator = SiteGenerator(config)
        
        # Clean output directory if requested
        if args.clean:
            logging.info("Cleaning output directory...")
            generator.clean_output_dir()
        
        # Generate the site
        logging.info(f"Building site: {config.title}")
        generator.generate_site()
        
        # Report results
        logging.info(f"Site build completed successfully!")
        logging.info(f"- Total posts: {generator.get_total_posts()}")
        logging.info(f"- Total pages: {generator.get_total_pages()}")
        logging.info(f"- Output directory: {config.output_dir}")
        
        return 0
        
    except Exception as e:
        logging.error(f"Build failed with error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Make the script executable on Unix-like systems
    sys.exit(main())