#!/usr/bin/env python3
"""
Static site generator CLI for Salas Blog
"""
import sys
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import json
import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader

from utils import (
    format_date,
    create_excerpt,
    parse_date_for_sorting,
    process_markdown_to_html,
    parse_frontmatter_file,
    generate_url_from_filename,
    sort_posts_by_date,
    load_markdown_files_from_directory,
    safe_get_filename_stem
)


class SiteGenerator:
    def __init__(self, theme="winer"):
        self.root_dir = Path.cwd()
        self.content_dir = self.root_dir / "content"
        self.blog_dir = self.content_dir / "blog"
        self.raindrops_dir = self.content_dir / "raindrops"
        self.pages_dir = self.content_dir / "pages"
        self.output_dir = self.root_dir / "output"
        
        # Theme support
        self.theme = theme
        self.themes_dir = self.root_dir / "themes"
        self.templates_dir = self.themes_dir / theme / "templates"
        self.static_dir = self.themes_dir / theme / "static"
        
        # Fallback to old structure if theme doesn't exist
        if not self.templates_dir.exists():
            print(f"⚠️  Theme '{theme}' not found, falling back to default templates")
            self.templates_dir = self.root_dir / "templates"
            self.static_dir = self.root_dir / "static"
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))
        self.jinja_env.filters['strftime'] = self.format_date
        self.markdown_processor = markdown.Markdown(extensions=['meta', 'codehilite', 'toc'])
    
    def format_date(self, date_str, format_str='%B %d, %Y'):
        """Custom Jinja2 filter for date formatting"""
        return format_date(date_str, format_str)
        
    def load_posts(self, content_type):
        """Load and parse markdown files from a directory"""
        posts = []
        if content_type == 'blog':
            content_dir = self.blog_dir
        elif content_type == 'raindrops':
            content_dir = self.raindrops_dir
        elif content_type == 'pages':
            content_dir = self.pages_dir
        else:
            return posts
        
        if not content_dir.exists():
            return posts
        
        for md_file in load_markdown_files_from_directory(content_dir):
            try:
                parsed = parse_frontmatter_file(md_file)
                filename = safe_get_filename_stem(md_file)
                
                # Extract frontmatter data
                post_data = {
                    'title': parsed['metadata'].get('title', filename),
                    'date': parsed['metadata'].get('date', ''),
                    'type': parsed['metadata'].get('type', content_type),
                    'category': parsed['metadata'].get('category', 'Uncategorized'),
                    'content': parsed['html_content'],
                    'raw_content': parsed['content'],
                    'filename': filename,
                    'url': generate_url_from_filename(filename, content_type)
                }
                
                # Create excerpt from content
                post_data['excerpt'] = create_excerpt(parsed['content'])
                
                posts.append(post_data)
                
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
        
        # Sort by date (newest first)
        return sort_posts_by_date(posts)
    
    def show_help(self):
        """Show very short help message"""
        print("bg.py [generate|reset|deploy|themes|help] [--theme THEME_NAME]")
        print("Commands:")
        print("  generate  - Process markdown files and generate static HTML site")
        print("  reset     - Delete all generated files")
        print("  deploy    - Deploy site to Fly.io")
        print("  themes    - List available themes")
        print("  help      - Show this help message")
        print()
        print("Themes: winer (scripting.com style), salas (original style)")
    
    def generate(self):
        """Process all markdown files and generate static HTML site"""
        print("Generating site...")
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Copy static files
        if self.static_dir.exists():
            output_static = self.output_dir / "static"
            if output_static.exists():
                shutil.rmtree(output_static)
            shutil.copytree(self.static_dir, output_static)
            print("✓ Copied static files")
        
        # Load all content
        blog_posts = self.load_posts('blog')
        raindrops = self.load_posts('raindrops')
        pages = self.load_posts('pages')
        all_posts = blog_posts + raindrops
        
        print(f"✓ Loaded {len(blog_posts)} blog posts, {len(raindrops)} raindrops, {len(pages)} pages")
        
        # Prepare navigation data from pages
        nav_pages = [{'title': page['title'], 'url': page['url']} for page in pages]
        
        # Generate home page
        self.generate_home_page(blog_posts, raindrops, nav_pages)
        
        # Generate listing pages
        self.generate_listing_pages(blog_posts, 'blog', nav_pages)
        self.generate_listing_pages(raindrops, 'raindrops', nav_pages)
        
        # Generate individual post pages
        self.generate_post_pages(blog_posts, 'blog', nav_pages)
        self.generate_post_pages(raindrops, 'raindrops', nav_pages)
        
        # Generate individual pages (about, etc.)
        self.generate_individual_pages(pages, nav_pages)
        
        # Generate search index
        self.generate_search_json(all_posts)
        
        print("✓ Site generated successfully")
    
    def generate_home_page(self, blog_posts, raindrops, nav_pages):
        """Generate the home page"""
        template = self.jinja_env.get_template('home.html')
        
        # Get recent posts (limit to 5 each)
        recent_posts = blog_posts[:5]
        recent_raindrops = raindrops[:5]
        
        html = template.render(
            recent_posts=recent_posts,
            recent_raindrops=recent_raindrops,
            nav_pages=nav_pages,
            current_year=datetime.now().year
        )
        
        output_file = self.output_dir / "index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print("✓ Generated home page")
    
    def generate_post_pages(self, posts, content_type, nav_pages):
        """Generate individual post pages"""
        if not posts:
            return
            
        template_name = 'blog_post.html' if content_type == 'blog' else 'raindrop_post.html'
        template = self.jinja_env.get_template(template_name)
        
        # Create output directory for posts
        output_dir = self.output_dir / content_type
        output_dir.mkdir(exist_ok=True)
        
        for i, post in enumerate(posts):
            # Get previous and next posts for navigation
            prev_post = posts[i + 1] if i + 1 < len(posts) else None
            next_post = posts[i - 1] if i > 0 else None
            
            html = template.render(
                post=post,
                prev_post=prev_post,
                next_post=next_post,
                nav_pages=nav_pages,
                current_year=datetime.now().year
            )
            
            output_file = output_dir / f"{post['filename']}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
        
        print(f"✓ Generated {len(posts)} {content_type} pages")
    
    def generate_search_json(self, all_posts):
        """Generate search index JSON file"""
        search_data = []
        
        for post in all_posts:
            search_data.append({
                'title': post['title'],
                'content': post['raw_content'][:500],  # Limit content for search
                'category': post['category'],
                'url': post['url'],
                'type': post['type']
            })
        
        search_file = self.output_dir / "search.json"
        with open(search_file, 'w', encoding='utf-8') as f:
            json.dump(search_data, f, indent=2)
        
        print(f"✓ Generated search index ({len(search_data)} entries)")
    
    def generate_listing_pages(self, posts, content_type, nav_pages):
        """Generate listing pages for blog and raindrops"""
        if content_type == 'blog':
            template = self.jinja_env.get_template('blog_list.html')
            output_file = self.output_dir / "blog" / "index.html"
        elif content_type == 'raindrops':
            template = self.jinja_env.get_template('raindrops_list.html')
            output_file = self.output_dir / "raindrops" / "index.html"
        else:
            return
        
        # Ensure directory exists
        output_file.parent.mkdir(exist_ok=True)
        
        html = template.render(
            posts=posts,
            nav_pages=nav_pages,
            current_year=datetime.now().year
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ Generated {content_type} listing page")
    
    def generate_individual_pages(self, pages, nav_pages):
        """Generate individual pages (like about.html)"""
        if not pages:
            return
            
        template = self.jinja_env.get_template('page.html')
        
        for page in pages:
            html = template.render(
                page=page,
                nav_pages=nav_pages,
                current_year=datetime.now().year
            )
            
            output_file = self.output_dir / f"{page['filename']}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
        
        print(f"✓ Generated {len(pages)} individual pages")
    
    def reset(self):
        """Delete all generated files"""
        print("Resetting site...")
        
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            print("✓ Deleted output directory")
        else:
            print("✓ Output directory already clean")
    
    def deploy(self):
        """Deploy site to Fly.io"""
        print("Deploying to Fly.io...")
        
        # Check if site is generated
        if not self.output_dir.exists():
            print("❌ Site not generated. Run 'python b.py generate' first.")
            return False
        
        try:
            # Run fly deploy
            result = subprocess.run(["fly", "deploy"], 
                                  capture_output=True, text=True, cwd=self.root_dir)
            
            if result.returncode == 0:
                print("✓ Deployed successfully")
                return True
            else:
                print(f"❌ Deploy failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("❌ Fly CLI not found. Install with: curl -L https://fly.io/install.sh | sh")
            return False
        except Exception as e:
            print(f"❌ Deploy error: {e}")
            return False


def main():
    # Check for theme parameter
    theme = "winer"  # default theme
    
    # Look for --theme parameter
    args = sys.argv[1:]
    if "--theme" in args:
        theme_index = args.index("--theme")
        if theme_index + 1 < len(args):
            theme = args[theme_index + 1]
            # Remove theme args from argv
            args = args[:theme_index] + args[theme_index + 2:]
        else:
            print("❌ --theme requires a theme name")
            sys.exit(1)
    
    generator = SiteGenerator(theme=theme)
    
    # Handle command line arguments
    if len(args) == 0:
        # No arguments - show help
        generator.show_help()
        return
    
    command = args[0].lower()
    
    if command == "generate":
        print(f"🎨 Using theme: {theme}")
        generator.generate()
    elif command == "reset":
        generator.reset()
    elif command == "deploy":
        generator.deploy()
    elif command == "themes":
        # List available themes
        themes_dir = Path.cwd() / "themes"
        if themes_dir.exists():
            print("Available themes:")
            for theme_dir in themes_dir.iterdir():
                if theme_dir.is_dir():
                    print(f"  - {theme_dir.name}")
        else:
            print("No themes directory found")
    elif command in ["help", "-h", "--help"]:
        generator.show_help()
    else:
        print(f"Unknown command: {command}")
        generator.show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()