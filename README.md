# Static Blog Generator

A simple static blog system that generates HTML from Markdown content.

## Usage

### Build the site

```bash
python3 bin/build.py
```

### Build with options

```bash
# Clean build (remove old output first)
python3 bin/build.py --clean

# Build with custom configuration
python3 bin/build.py --title "My Blog" --posts-per-page 10
```

### Add content

1. Create new Markdown files in `content/posts/`
2. Use frontmatter for metadata:

```markdown
---
title: My Post
date: 2026-07-07
description: Post description
---

# My Post

Content in Markdown format.
```

3. Add media files alongside your Markdown files in `content/posts/`

### Deploy to GitHub Pages

The generated HTML files are placed in `docs/`. 
GitHub Pages will automatically serve this directory when enabled.

## Project Structure

- `bin/build.py` - Build script
- `lib/` - Python library code
- `templates/` - HTML templates
- `content/posts/` - Markdown content and media files
- `docs/` - Generated output (committed to git for GitHub Pages)

## Features

- Markdown to HTML conversion
- Automatic pagination (5 posts per page by default)
- Clean, responsive CSS
- No JavaScript required
- Static output suitable for GitHub Pages
