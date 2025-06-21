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


class SiteGenerator:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.content_dir = self.root_dir / "content"
        self.blog_dir = self.content_dir / "blog"
        self.raindrops_dir = self.content_dir / "raindrops"
        self.pages_dir = self.content_dir / "pages"
        self.output_dir = self.root_dir / "output"
        self.templates_dir = self.root_dir / "templates"
        self.static_dir = self.root_dir / "static"
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))
        self.jinja_env.filters['strftime'] = self.format_date
        self.markdown_processor = markdown.Markdown(extensions=['meta', 'codehilite', 'toc'])
    
    def format_date(self, date_str, format_str='%B %d, %Y'):
        """Custom Jinja2 filter for date formatting"""
        if not date_str:
            return ''
        try:
            # Try to parse the date string
            if isinstance(date_str, str):
                from datetime import datetime
                # Assume ISO format YYYY-MM-DD
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.strftime(format_str)
            return date_str
        except:
            return date_str
        
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
        
        for md_file in content_dir.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                
                # Extract frontmatter data
                post_data = {
                    'title': post.metadata.get('title', md_file.stem),
                    'date': post.metadata.get('date', ''),
                    'type': post.metadata.get('type', content_type),
                    'category': post.metadata.get('category', 'Uncategorized'),
                    'content': markdown.markdown(post.content),
                    'raw_content': post.content,
                    'filename': md_file.stem,
                    'url': f"/{md_file.stem}.html" if content_type == 'pages' else f"/{content_type}/{md_file.stem}.html"
                }
                
                # Create excerpt from content (first 150 chars)
                plain_content = post.content.replace('\n', ' ').strip()
                post_data['excerpt'] = plain_content[:150] + ('...' if len(plain_content) > 150 else '')
                
                posts.append(post_data)
                
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
        
        # Sort by date (newest first) - handle date strings properly
        def get_sort_date(post):
            date_str = post['date']
            if not date_str:
                return datetime.min
            try:
                return datetime.strptime(str(date_str), '%Y-%m-%d')
            except:
                return datetime.min
        
        posts.sort(key=get_sort_date, reverse=True)
        return posts
    
    def show_help(self):
        """Show very short help message"""
        print("b.py [generate|reset|deploy]")
    
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
    generator = SiteGenerator()
    
    # Handle command line arguments
    if len(sys.argv) == 1:
        # No arguments - show help
        generator.show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "generate":
        generator.generate()
    elif command == "reset":
        generator.reset()
    elif command == "deploy":
        generator.deploy()
    elif command in ["help", "-h", "--help"]:
        generator.show_help()
    else:
        print(f"Unknown command: {command}")
        generator.show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()