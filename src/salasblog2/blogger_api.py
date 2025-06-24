"""
Blogger API (XML-RPC) implementation for Salasblog2
Supports Blogger API methods for compatibility with blog editors like Windows Live Writer and MarsEdit.
"""
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import frontmatter
import re
from .generator import SiteGenerator


class BloggerAPI:
    """Blogger API implementation supporting standard Blogger XML-RPC methods"""
    
    def __init__(self):
        self.root_dir = Path.cwd()
        self.blog_dir = self.root_dir / "content" / "blog"
        self.blog_dir.mkdir(parents=True, exist_ok=True)
    
    def create_filename_from_title(self, title: str) -> str:
        """Create a safe filename from post title"""
        # Remove special characters and convert to lowercase
        safe_title = re.sub(r'[^\w\s-]', '', title.lower())
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        
        # Add date prefix
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{date_str}-{safe_title}.md"
    
    def blogger_newPost(self, appkey: str, blogid: str, username: str, password: str, 
                       content: str, publish: bool) -> str:
        """
        Blogger API: blogger.newPost
        Create a new blog post and return the post ID (filename)
        
        Args:
            appkey: Application key (ignored)
            blogid: Blog identifier 
            username: Username for authentication
            password: Password for authentication
            content: Post content (first line becomes title)
            publish: Whether to publish immediately
            
        Returns:
            str: Post ID (filename)
        """
        # Basic auth check (you'd want real auth in production)
        if not self._authenticate(username, password):
            raise Exception("Authentication failed")
        
        # Parse content to extract title
        lines = content.strip().split('\n')
        title = lines[0] if lines else "Untitled Post"
        body_content = '\n'.join(lines[1:]) if len(lines) > 1 else content
        
        # Create filename
        filename = self.create_filename_from_title(title)
        
        # Create frontmatter
        post = frontmatter.Post(body_content)
        post.metadata = {
            'title': title,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'type': 'blog',
            'category': 'General'
        }
        
        # Write file
        file_path = self.blog_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        # Regenerate site if published
        if publish:
            generator = SiteGenerator()
            generator.generate_site()
        
        return filename
    
    def blogger_editPost(self, appkey: str, postid: str, username: str, password: str,
                        content: str, publish: bool) -> bool:
        """
        Blogger API: blogger.editPost
        Edit an existing blog post
        
        Args:
            appkey: Application key (ignored)
            postid: Post ID (filename)
            username: Username for authentication
            password: Password for authentication
            content: New post content (first line becomes title)
            publish: Whether to publish immediately
            
        Returns:
            bool: True if successful
        """
        if not self._authenticate(username, password):
            raise Exception("Authentication failed")
        
        file_path = self.blog_dir / postid
        if not file_path.exists():
            raise Exception("Post not found")
        
        # Parse content to extract title
        lines = content.strip().split('\n')
        title = lines[0] if lines else "Untitled Post"
        body_content = '\n'.join(lines[1:]) if len(lines) > 1 else content
        
        # Update post
        post = frontmatter.Post(body_content)
        post.metadata = {
            'title': title,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'type': 'blog',
            'category': 'General'
        }
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        # Regenerate site if published
        if publish:
            generator = SiteGenerator()
            generator.generate_site()
        
        return True
    
    def blogger_deletePost(self, appkey: str, postid: str, username: str, password: str,
                          publish: bool) -> bool:
        """
        Blogger API: blogger.deletePost
        Delete a blog post
        
        Args:
            appkey: Application key (ignored)
            postid: Post ID (filename)
            username: Username for authentication
            password: Password for authentication
            publish: Whether to regenerate site after deletion
            
        Returns:
            bool: True if successful
        """
        if not self._authenticate(username, password):
            raise Exception("Authentication failed")
        
        file_path = self.blog_dir / postid
        if not file_path.exists():
            raise Exception("Post not found")
        
        file_path.unlink()
        
        # Regenerate site if published
        if publish:
            generator = SiteGenerator()
            generator.generate_site()
        
        return True
    
    def blogger_getRecentPosts(self, appkey: str, blogid: str, username: str, password: str,
                              numberOfPosts: int) -> list:
        """
        Blogger API: blogger.getRecentPosts
        Get recent blog posts
        
        Args:
            appkey: Application key (ignored)
            blogid: Blog identifier
            username: Username for authentication
            password: Password for authentication
            numberOfPosts: Maximum number of posts to return
            
        Returns:
            list: List of post dictionaries with postid, title, content, dateCreated, userid
        """
        if not self._authenticate(username, password):
            raise Exception("Authentication failed")
        
        posts = []
        for md_file in sorted(self.blog_dir.glob("*.md"), reverse=True)[:numberOfPosts]:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                
                posts.append({
                    'postid': md_file.name,
                    'title': post.metadata.get('title', 'Untitled'),
                    'content': post.content,
                    'dateCreated': post.metadata.get('date', ''),
                    'userid': username
                })
            except Exception:
                continue
        
        return posts
    
    def blogger_getUsersBlogs(self, appkey: str, username: str, password: str) -> list:
        """
        Blogger API: blogger.getUsersBlogs
        Get user's blogs
        
        Args:
            appkey: Application key (ignored)
            username: Username for authentication
            password: Password for authentication
            
        Returns:
            list: List of blog dictionaries with blogid, blogName, url
        """
        if not self._authenticate(username, password):
            raise Exception("Authentication failed")
        
        return [{
            'blogid': 'salasblog2',
            'blogName': 'Salas Blog',
            'url': '/'
        }]
    
    def _authenticate(self, username: str, password: str) -> bool:
        """Basic authentication check"""
        import os
        
        # Check environment variables for credentials
        expected_username = os.getenv('BLOG_USERNAME', 'admin')
        expected_password = os.getenv('BLOG_PASSWORD', 'password')
        
        # Allow the configured credentials
        if username == expected_username and password == expected_password:
            return True
            
        # Fallback: allow any non-empty credentials for development
        return bool(username and password)