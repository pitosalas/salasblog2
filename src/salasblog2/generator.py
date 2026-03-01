"""
Static site generator for Salas Blog.
"""
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import json
import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader

from .utils import (
    format_date,
    create_excerpt,
    create_excerpt_with_info,
    extract_first_paragraph,
    parse_date_for_sorting,
    process_markdown_to_html,
    parse_frontmatter_file,
    generate_url_from_filename,
    sort_posts_by_date,
    group_posts_by_month,
    load_markdown_files_from_directory,
    get_markdown_processor,
    slugify_tag,
    slugify_collection,
    extract_unique_collections
)


class SiteGenerator:
    def __init__(self):
        self.root_dir = Path.cwd()
        # Use persistent volume as source of truth for content, fallback to local
        volume_content_dir = Path("/data/content")
        if volume_content_dir.exists():
            self.content_dir = volume_content_dir
        else:
            self.content_dir = self.root_dir / "content"
        
        self.blog_dir = self.content_dir / "blog"
        self.raindrops_dir = self.content_dir / "raindrops"
        self.pages_dir = self.content_dir / "pages"
        self.output_dir = self.root_dir / "output"
        
        # Use default templates and static directories
        self.templates_dir = self.root_dir / "templates"
        self.static_dir = self.root_dir / "static"
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))
        self.jinja_env.filters['strftime'] = self.format_date
        self.jinja_env.filters['dd_mm_yyyy'] = lambda date_str: format_date(date_str, '%d-%m-%Y')
        self.jinja_env.filters['group_by_month'] = group_posts_by_month
        self.jinja_env.filters['markdown'] = self.markdown_to_html
        self.jinja_env.filters['slugify'] = slugify_tag
        self.jinja_env.filters['slugify_collection'] = slugify_collection
        self.jinja_env.globals['NOTE_TRUNCATE_LENGTH'] = 300
        # Use the same markdown processor as utils.py for consistency
        self.markdown_processor = get_markdown_processor()
    
    def format_date(self, date_str, format_str='%B %d, %Y'):
        """Custom Jinja2 filter for date formatting"""
        return format_date(date_str, format_str)
    
    def markdown_to_html(self, text):
        """Custom Jinja2 filter for converting markdown to HTML"""
        return process_markdown_to_html(text)
        
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
                filename = md_file.stem
                
                # Extract frontmatter data
                # Use a clear placeholder when title is missing from frontmatter
                title = parsed['metadata'].get('title')
                if not title:
                    title = f"placeholder title: {filename.replace('_', ' ').replace('-', ' ').title()}"
                
                post_data = {
                    'title': title,
                    'date': parsed['metadata'].get('date', ''),
                    'type': parsed['metadata'].get('type', content_type),

                    'content': parsed['html_content'],
                    'raw_content': parsed['content'],
                    'filename': filename,
                    'url': generate_url_from_filename(filename, content_type),
                    'tags': parsed['metadata'].get('tags', [])
                }
                
                # Add raindrop-specific fields if they exist
                if content_type == 'raindrops':
                    # Extract notes from content if not in frontmatter
                    note = parsed['metadata'].get('note', '')
                    if not note and '**Notes:**' in parsed['content']:
                        # Extract notes from content
                        lines = parsed['content'].split('\n')
                        note_start = False
                        note_lines = []
                        for line in lines:
                            if line.strip() == '**Notes:**':
                                note_start = True
                                continue
                            elif note_start and line.strip().startswith('**') and line.strip().endswith('**'):
                                # Hit another section, stop collecting notes
                                break
                            elif note_start:
                                note_lines.append(line)
                        note = '\n'.join(note_lines).strip()
                    
                    post_data.update({
                        'cover': parsed['metadata'].get('cover', ''),
                        'domain': parsed['metadata'].get('domain', ''),
                        'media': parsed['metadata'].get('media', []),
                        'raindrop_type': parsed['metadata'].get('raindrop_type', ''),
                        'important': parsed['metadata'].get('important', False),
                        'broken': parsed['metadata'].get('broken', False),
                        'tags': parsed['metadata'].get('tags', []),
                        'raindrop_url': parsed['metadata'].get('url', ''),  # Original URL
                        'collection': parsed['metadata'].get('collection', ''),
                        'note': note
                    })
                
                # Create excerpt - prefer frontmatter excerpt, fallback to content
                frontmatter_excerpt = parsed['metadata'].get('excerpt', '')
                if frontmatter_excerpt:
                    post_data['excerpt'] = frontmatter_excerpt
                    post_data['is_truncated'] = False
                elif content_type == 'pages':
                    post_data['excerpt'] = extract_first_paragraph(parsed['content'])
                    post_data['is_truncated'] = False
                elif content_type == 'raindrops':
                    # Raindrop body contains raw metadata labels (**URL:**, **Type:**, etc.)
                    # Note and URL are already rendered separately by the template
                    post_data['excerpt'] = ''
                    post_data['is_truncated'] = False
                else:
                    excerpt, is_truncated = create_excerpt_with_info(parsed['content'])
                    post_data['excerpt'] = excerpt
                    post_data['is_truncated'] = is_truncated
                
                posts.append(post_data)
                
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
        
        # Sort by date (newest first)
        return sort_posts_by_date(posts)
    
    def generate_search_index(self, all_posts):
        """Generate search index JSON"""
        search_data = []
        for post in all_posts:
            search_item = {
                'title': post['title'],
                'url': post['url'],
                'type': post['type'],
                'excerpt': post['excerpt'],
                'content': post['raw_content'][:500] + '...' if len(post['raw_content']) > 500 else post['raw_content']
            }
            search_data.append(search_item)
        
        search_file = self.output_dir / "search.json"
        with open(search_file, 'w', encoding='utf-8') as f:
            json.dump(search_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Generated search index: {search_file}")
    
    def generate_404_page(self):
        """Generate 404 error page"""
        try:
            template = self.jinja_env.get_template('404.html')
            
            context = {
                'title': 'Page Not Found',
                'site_title': 'Pito Salas Blog',
                'navigation': self.get_navigation_items(),
                'current_year': datetime.now().year
            }
            
            html_content = template.render(**context)
            
            # Write to output directory
            output_file = self.output_dir / "404.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print("✓ Generated 404 error page")
            
        except Exception as e:
            print(f"⚠️  Could not generate 404 page: {e}")
            # Continue without 404 page - server will use fallback
    
    def copy_static_files(self):
        """Copy static files to output directory"""
        static_output_dir = self.output_dir / "static"
        
        # Remove existing static directory
        if static_output_dir.exists():
            shutil.rmtree(static_output_dir)
        
        # Copy static files
        if self.static_dir.exists():
            shutil.copytree(self.static_dir, static_output_dir)
            print(f"✓ Copied static files")
        else:
            print(f"⚠️  No static files found")
    
    def render_template(self, template_name, context):
        """Render a Jinja2 template with context"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(context)
        except Exception as e:
            print(f"Error rendering template {template_name}: {e}")
            return ""
    
    def generate_individual_posts(self, posts, content_type):
        """Generate individual post pages"""
        template_name = {
            'blog': 'blog_post.html',
            'raindrops': 'raindrop_post.html', 
            'pages': 'page.html'
        }.get(content_type, 'page.html')
        
        for i, post in enumerate(posts):
            prev_post = posts[i + 1] if i + 1 < len(posts) else None
            next_post = posts[i - 1] if i > 0 else None
            context = {
                'post': post,
                'page': post,  # Some templates expect 'page' instead of 'post'
                'site_title': 'Pito Salas Blog',
                'navigation': self.get_navigation_items(),
                'prev_post': prev_post,
                'next_post': next_post,
            }
            
            html_content = self.render_template(template_name, context)
            
            if content_type == 'pages':
                # Pages go in root output directory
                output_file = self.output_dir / f"{post['filename']}.html"
            else:
                # Blog posts and raindrops go in subdirectories
                output_subdir = self.output_dir / content_type
                output_subdir.mkdir(exist_ok=True)
                output_file = output_subdir / f"{post['filename']}.html"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        print(f"✓ Generated {len(posts)} {content_type} pages")
    
    def generate_listing_pages(self, posts, content_type, collections=None, collection_counts=None):
        """Generate paginated listing pages for blog and raindrops"""
        if content_type == 'pages':
            return  # Pages don't have listing pages

        posts = sorted(posts, key=lambda x: x.get('date', ''), reverse=True)
        posts_per_page = 20  # Show 20 posts per page
        total_posts = len(posts)
        total_pages = max(1, (total_posts + posts_per_page - 1) // posts_per_page)  # Ensure at least 1 page

        template_name = f"{content_type}_list.html"

        # Create subdirectory for listing
        output_subdir = self.output_dir / content_type
        output_subdir.mkdir(exist_ok=True)

        # Generate each page
        for page_num in range(1, total_pages + 1):
            start_idx = (page_num - 1) * posts_per_page
            end_idx = start_idx + posts_per_page
            page_posts = posts[start_idx:end_idx]

            # Build pagination context
            pagination = {
                'current_page': page_num,
                'total_pages': total_pages,
                'has_prev': page_num > 1,
                'has_next': page_num < total_pages,
                'prev_url': self._get_page_url(content_type, page_num - 1) if page_num > 1 else None,
                'next_url': self._get_page_url(content_type, page_num + 1) if page_num < total_pages else None,
                'page_urls': [self._get_page_url(content_type, p) for p in range(1, total_pages + 1)]
            }

            context = {
                'posts': page_posts,
                'content_type': content_type,
                'site_title': 'Pito Salas Blog',
                'navigation': self.get_navigation_items(),
                'pagination': pagination,
                'total_posts': total_posts,
                'collections': collections or [],
                'collection_counts': collection_counts or {}
            }
            
            html_content = self.render_template(template_name, context)
            
            # First page goes to index.html, others to page-N.html
            if page_num == 1:
                output_file = output_subdir / "index.html"
            else:
                output_file = output_subdir / f"page-{page_num}.html"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        print(f"✓ Generated {content_type} listing pages ({total_pages} pages, {total_posts} posts)")
    
    def _get_page_url(self, content_type, page_num, collection_slug=None):
        """Get URL for a specific page number, optionally filtered by collection"""
        base = f"/{content_type}"
        if collection_slug:
            base = f"/{content_type}/{collection_slug}"

        if page_num == 1:
            return f"{base}/"
        else:
            return f"{base}/page-{page_num}.html"

    def generate_collection_filtered_pages(self, raindrops, collections, collection_counts=None):
        """Generate collection-filtered listing pages for raindrops"""
        if not collections:
            return

        template_name = "raindrops_list.html"
        posts_per_page = 20

        for collection in collections:
            collection_slug = slugify_tag(collection)
            filtered_raindrops = [r for r in raindrops if r.get('collection') == collection]

            if not filtered_raindrops:
                continue

            total_posts = len(filtered_raindrops)
            total_pages = max(1, (total_posts + posts_per_page - 1) // posts_per_page)

            # Create collection subdirectory
            collection_dir = self.output_dir / "raindrops" / collection_slug
            collection_dir.mkdir(parents=True, exist_ok=True)

            # Generate each page
            for page_num in range(1, total_pages + 1):
                start_idx = (page_num - 1) * posts_per_page
                end_idx = start_idx + posts_per_page
                page_posts = filtered_raindrops[start_idx:end_idx]

                pagination = {
                    'current_page': page_num,
                    'total_pages': total_pages,
                    'has_prev': page_num > 1,
                    'has_next': page_num < total_pages,
                    'prev_url': self._get_page_url('raindrops', page_num - 1, collection_slug) if page_num > 1 else None,
                    'next_url': self._get_page_url('raindrops', page_num + 1, collection_slug) if page_num < total_pages else None,
                    'page_urls': [self._get_page_url('raindrops', p, collection_slug) for p in range(1, total_pages + 1)]
                }

                context = {
                    'posts': page_posts,
                    'content_type': 'raindrops',
                    'site_title': 'Pito Salas Blog',
                    'navigation': self.get_navigation_items(),
                    'pagination': pagination,
                    'total_posts': total_posts,
                    'collections': collections,
                    'collection_counts': collection_counts or {},
                    'current_collection': collection
                }

                html_content = self.render_template(template_name, context)

                if page_num == 1:
                    output_file = collection_dir / "index.html"
                else:
                    output_file = collection_dir / f"page-{page_num}.html"

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)

    def get_navigation_items(self):
        """Get simplified navigation items"""
        nav_items = []
        
        # Simplified navigation structure
        nav_items.append({'title': 'Home', 'url': '/'})
        nav_items.append({'title': 'Blog', 'url': '/blog/'})
        nav_items.append({'title': 'Link Blog', 'url': '/raindrops/'})
        nav_items.append({'title': 'Pages', 'url': '/pages/'})
        
        return nav_items
    
    def generate_home_page(self, blog_posts, raindrops):
        """Generate the home page"""
        # Get recent posts for home page
        posts_count = int(os.environ.get("HOME_POSTS_COUNT", "5"))
        sorted_blog = sorted(blog_posts, key=lambda x: x.get('date', ''), reverse=True)
        sorted_raindrops = sorted(raindrops, key=lambda x: x.get('date', ''), reverse=True)
        recent_blog_posts = sorted_blog[:posts_count] if sorted_blog else []
        recent_raindrops = sorted_raindrops[:posts_count] if sorted_raindrops else []
        
        context = {
            'recent_posts': recent_blog_posts,
            'recent_blog_posts': recent_blog_posts,
            'recent_raindrops': recent_raindrops,
            'site_title': 'Pito Salas Blog',
            'navigation': self.get_navigation_items()
        }
        
        html_content = self.render_template('home.html', context)
        
        output_file = self.output_dir / "index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✓ Generated home page")
    
    def generate_overview_page(self):
        """Generate overview page with recent blog posts and raindrops"""
        # Load recent blog posts (limit to 5)
        blog_posts = self.load_posts('blog')
        blog_posts.sort(key=lambda x: x.get('date', ''), reverse=True)
        recent_blog_posts = blog_posts[:5]
        
        # Load recent raindrops (limit to 15)
        raindrops = self.load_posts('raindrops')
        raindrops.sort(key=lambda x: x.get('date', ''), reverse=True)
        recent_raindrops = raindrops[:15]
        
        context = {
            'blog_posts': recent_blog_posts,
            'raindrops': recent_raindrops,
            'site_title': 'Pito Salas Blog',
            'navigation': self.get_navigation_items()
        }
        
        html_content = self.render_template('overview.html', context)
        
        output_file = self.output_dir / "overview.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✓ Generated overview page")
    
    def generate_overview_as_home(self):
        """Generate overview page as the home page (index.html)"""
        # Load recent blog posts (limit to 5)
        blog_posts = self.load_posts('blog')
        blog_posts.sort(key=lambda x: x.get('date', ''), reverse=True)
        recent_blog_posts = blog_posts[:5]
        
        # Load recent raindrops (limit to 15)
        raindrops = self.load_posts('raindrops')
        raindrops.sort(key=lambda x: x.get('date', ''), reverse=True)
        recent_raindrops = raindrops[:15]
        
        context = {
            'blog_posts': recent_blog_posts,
            'raindrops': recent_raindrops,
            'site_title': 'Pito Salas Blog',
            'navigation': self.get_navigation_items()
        }
        
        html_content = self.render_template('overview.html', context)
        
        output_file = self.output_dir / "index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✓ Generated index.html (overview layout)")
    
    def generate_pages_listing(self, pages):
        """Generate the pages listing page"""
        # Sort pages alphabetically by title
        sorted_pages = sorted(pages, key=lambda p: p['title'].lower())
        
        context = {
            'pages': sorted_pages,
            'site_title': 'Pito Salas Blog',
            'navigation': self.get_navigation_items(),
            'title': 'Pages'
        }
        
        html_content = self.render_template('pages_list.html', context)
        
        # Create pages subdirectory
        pages_output_dir = self.output_dir / "pages"
        pages_output_dir.mkdir(exist_ok=True)
        
        output_file = pages_output_dir / "index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✓ Generated pages listing")
    
    def reset_output(self):
        """Remove all generated files"""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            print(f"✓ Deleted output directory: {self.output_dir}")
        else:
            print("✓ No output directory to delete")
    
    
    def deploy_to_fly(self):
        """Deploy to Fly.io"""
        try:
            result = subprocess.run(['fly', 'deploy'], check=True)
            print("✓ Successfully deployed to Fly.io")
        except subprocess.CalledProcessError as e:
            print(f"✗ Deployment failed (exit code {e.returncode})")
        except FileNotFoundError:
            print("✗ 'fly' command not found. Please install Fly CLI first.")
    
    def generate_tag_pages(self, posts, extra_posts=None):
        """Generate one tag index page per unique tag across blog and raindrop posts."""
        all_tagged = list(posts) + list(extra_posts or [])
        tags_by_slug = {}
        for post in all_tagged:
            for tag in post.get('tags', []):
                slug = slugify_tag(tag)
                if slug not in tags_by_slug:
                    tags_by_slug[slug] = {'name': tag, 'posts': []}
                tags_by_slug[slug]['posts'].append(post)

        for slug, data in tags_by_slug.items():
            tag_dir = self.output_dir / "tags" / slug
            tag_dir.mkdir(parents=True, exist_ok=True)
            context = {
                'tag': data['name'],
                'posts': sort_posts_by_date(data['posts']),
                'site_title': 'Pito Salas Blog',
                'navigation': self.get_navigation_items()
            }
            html_content = self.render_template('tag_page.html', context)
            with open(tag_dir / "index.html", 'w', encoding='utf-8') as f:
                f.write(html_content)

        print(f"✓ Generated {len(tags_by_slug)} tag pages")

    def generate_site(self):
        """Generate the complete static site"""
        print(f"🚀 Starting site generation")
        print(f"📁 Templates: {self.templates_dir}")
        print(f"📁 Static files: {self.static_dir}")
        print(f"📁 Output: {self.output_dir}")
        print()
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        print(f"✓ Created output directory")
        
        # Load all content
        print("📖 Loading content...")
        blog_posts = self.load_posts('blog')
        raindrops = self.load_posts('raindrops')
        pages = self.load_posts('pages')

        print(f"✓ Loaded {len(blog_posts)} blog posts")
        print(f"✓ Loaded {len(raindrops)} raindrops")
        print(f"✓ Loaded {len(pages)} pages")

        # Extract unique collections from raindrops
        collections = extract_unique_collections(raindrops)
        print(f"✓ Found {len(collections)} unique collections")
        
        # Calculate collection counts
        collection_counts = {}
        for collection in collections:
            count = len([r for r in raindrops if r.get('collection') == collection])
            collection_counts[collection] = count
        print()
        
        # Generate individual posts
        print("🔨 Generating individual pages...")
        self.generate_individual_posts(blog_posts, 'blog')
        self.generate_individual_posts(raindrops, 'raindrops')
        self.generate_individual_posts(pages, 'pages')
        print()
        
        # Generate listing pages
        print("📋 Generating listing pages...")
        self.generate_listing_pages(blog_posts, 'blog')
        self.generate_listing_pages(raindrops, 'raindrops', collections, collection_counts)
        self.generate_collection_filtered_pages(raindrops, collections, collection_counts)
        print()

        # Generate tag pages
        print("🏷️  Generating tag pages...")
        self.generate_tag_pages(blog_posts, raindrops)
        print()
        
        # Generate home page
        print("🏠 Generating home page...")
        self.generate_home_page(blog_posts, raindrops)
        print()
        
        # Generate overview page
        print("📊 Generating overview page...")
        self.generate_overview_page()
        print()
        
        # Generate pages listing
        print("📄 Generating pages listing...")
        self.generate_pages_listing(pages)
        print()
        
        # Generate search index
        print("🔍 Generating search index...")
        all_posts = blog_posts + raindrops + pages
        self.generate_search_index(all_posts)
        print()
        
        # Generate 404 error page
        print("🚫 Generating 404 page...")
        self.generate_404_page()
        print()
        
        # Copy static files
        print("📋 Copying static files...")
        self.copy_static_files()
        print()
        
        total_files = len(blog_posts) + len(raindrops) + len(pages)
        print(f"✅ Site generation complete!")
        print(f"📊 Generated {total_files} total content files")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🌐 Ready to serve or deploy!")
    
    def incremental_regenerate_post(self, post_filename: str, content_type: str = 'blog'):
        """Incrementally regenerate site after a single post change."""
        print(f"🔄 Incremental regeneration for {content_type}: {post_filename}")
        
        # Create output directory if needed
        self.output_dir.mkdir(exist_ok=True)
        
        # Load all content (needed for listings and search)
        blog_posts = self.load_posts('blog')
        raindrops = self.load_posts('raindrops') 
        pages = self.load_posts('pages')
        
        # Find the specific post that changed
        content_posts = {'blog': blog_posts, 'raindrops': raindrops, 'pages': pages}[content_type]
        changed_post = next((p for p in content_posts if p['filename'] == post_filename.replace('.md', '')), None)
        
        if changed_post:
            # Regenerate the individual post
            self.generate_individual_posts([changed_post], content_type)
            print(f"✓ Regenerated individual {content_type} post")
        
        # Regenerate the listing page for this content type
        if content_type in ['blog', 'raindrops']:
            self.generate_listing_pages(content_posts, content_type)
            print(f"✓ Regenerated {content_type} listing page")
        
        # Regenerate home page (shows recent posts from blog and raindrops)
        self.generate_home_page(blog_posts, raindrops)
        print(f"✓ Regenerated home page")
        
        # Regenerate search index (includes all posts)
        all_posts = blog_posts + raindrops + pages
        self.generate_search_index(all_posts)
        print(f"✓ Regenerated search index")
        
        print(f"✅ Incremental regeneration complete!")
    
    def incremental_regenerate_after_deletion(self, post_filename: str, content_type: str = 'blog'):
        """Incrementally regenerate site after a post deletion."""
        print(f"🗑️ Incremental regeneration after {content_type} deletion: {post_filename}")
        
        # Create output directory if needed  
        self.output_dir.mkdir(exist_ok=True)
        
        # Remove the individual post file from output
        if content_type == 'pages':
            post_output_file = self.output_dir / f"{post_filename.replace('.md', '')}.html"
        else:
            post_output_file = self.output_dir / content_type / f"{post_filename.replace('.md', '')}.html"
        
        if post_output_file.exists():
            post_output_file.unlink()
            print(f"✓ Removed {content_type} output file: {post_output_file}")
        
        # Load remaining content
        blog_posts = self.load_posts('blog')
        raindrops = self.load_posts('raindrops')
        pages = self.load_posts('pages')
        
        # Regenerate listing page for this content type
        if content_type in ['blog', 'raindrops']:
            content_posts = {'blog': blog_posts, 'raindrops': raindrops}[content_type]
            self.generate_listing_pages(content_posts, content_type)
            print(f"✓ Regenerated {content_type} listing page")
        
        # Regenerate home page
        self.generate_home_page(blog_posts, raindrops)
        print(f"✓ Regenerated home page")
        
        # Regenerate search index
        all_posts = blog_posts + raindrops + pages
        self.generate_search_index(all_posts)
        print(f"✓ Regenerated search index")
        
        print(f"✅ Incremental deletion regeneration complete!")