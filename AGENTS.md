# Repository Guide for Agents

## Repository Contents

This repository contains a static blog generator system:

- **`bin/build.py`** - Main build script for generating the static site
- **`lib/`** - Python library code for the blog generator
  - `models.py` - Data models (Post, SiteConfig, Pagination)
  - `markdown_renderer.py` - Markdown to HTML conversion
  - `template_engine.py` - Custom template rendering engine
  - `generator.py` - Main site generation logic
- **`templates/`** - HTML templates for the blog
  - `base.html`, `index.html`, `archive.html`, `post.html`
  - `assets/style.css` - CSS styling
- **`content/posts/`** - Blog post content in Markdown format
- **`docs/`** - Generated static HTML output (GitHub Pages)
- **`.github/workflows/`** - GitHub Actions workflows
  - `deploy.yml` - Build and deploy to GitHub Pages
  - `lint.yml` - Run super-linter on pull requests

## Agent Instructions

**NEVER** mention yourself, your identity, or your existence in any of the following:

- Commit messages
- Author/co-author information
- File content or comments
- Documentation
- Anywhere in this repository

All commits should appear to be made by the repository owner. Do not add any attribution, co-authorship, or references to AI assistants, bots, or automated tools.

When creating commits, use only the actual author's information or leave author information empty. Do not add any generated-by, co-authored-by, or similar attribution lines.

This repository should appear to be entirely human-maintained.