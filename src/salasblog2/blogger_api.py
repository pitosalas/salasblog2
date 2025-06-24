"""
Blogger API (XML-RPC) implementation for Salasblog2
Supports Blogger API methods for compatibility with blog editors like Windows Live Writer and MarsEdit.
"""
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import frontmatter
import re
import logging
from .generator import SiteGenerator

# Set up logging
logger = logging.getLogger(__name__)


class BloggerAPI:
    """Blogger API implementation for XML-RPC compatibility with blog editors."""
    
    def __init__(self):
        self.root_dir = Path.cwd()
        self.blog_dir = self.root_dir / "content" / "blog"
        self.blog_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"BloggerAPI initialized, blog_dir: {self.blog_dir}")
    
    def create_filename_from_title(self, title: str) -> str:
        """Create a safe filename from post title."""
        # Remove special characters and convert to lowercase
        safe_title = re.sub(r'[^\w\s-]', '', title.lower())
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        
        # Add date prefix
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{date_str}-{safe_title}.md"
    
    def blogger_newPost(self, appkey: str, blogid: str, username: str, password: str, 
                       content: str, publish: bool) -> str:
        """Create a new blog post and return the post ID (filename)."""
        logger.info(f"blogger_newPost called: appkey={appkey}, blogid={blogid}, username={username}, publish={publish}")
        logger.debug(f"Content length: {len(content)}, content preview: {content[:100]}...")
        
        # Basic auth check (you'd want real auth in production)
        if not self._authenticate(username, password):
            logger.error("Authentication failed for newPost")
            raise Exception("Authentication failed")
        
        # Parse content to extract title
        lines = content.strip().split('\n')
        title = lines[0] if lines else "Untitled Post"
        body_content = '\n'.join(lines[1:]) if len(lines) > 1 else content
        logger.info(f"Parsed title: '{title}', body length: {len(body_content)}")
        
        # Create filename
        filename = self.create_filename_from_title(title)
        logger.info(f"Generated filename: {filename}")
        
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
        logger.info(f"Writing post to: {file_path}")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            logger.info(f"Post written successfully to {file_path}")
        except Exception as e:
            logger.error(f"Failed to write post: {e}")
            raise
        
        # Regenerate site if published
        if publish:
            logger.info("Incremental site regeneration after post creation")
            try:
                generator = SiteGenerator()
                generator.incremental_regenerate_post(filename, 'blog')
                logger.info("Incremental site regeneration completed")
            except Exception as e:
                logger.error(f"Incremental site regeneration failed: {e}")
                # Don't raise - post was still created successfully
        
        logger.info(f"blogger_newPost completed successfully, returning: {filename}")
        return filename
    
    def blogger_editPost(self, appkey: str, postid: str, username: str, password: str,
                        content: str, publish: bool) -> bool:
        """Edit an existing blog post."""
        logger.info(f"blogger_editPost called: postid={postid}, username={username}, publish={publish}")
        logger.debug(f"Content length: {len(content)}, content preview: {content[:100]}...")
        
        if not self._authenticate(username, password):
            logger.error("Authentication failed for editPost")
            raise Exception("Authentication failed")
        
        file_path = self.blog_dir / postid
        logger.info(f"Editing post at: {file_path}")
        if not file_path.exists():
            logger.error(f"Post not found: {file_path}")
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
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            logger.info(f"Post updated successfully: {file_path}")
        except Exception as e:
            logger.error(f"Failed to update post: {e}")
            raise
        
        # Regenerate site if published
        if publish:
            logger.info("Incremental site regeneration after post edit")
            try:
                generator = SiteGenerator()
                generator.incremental_regenerate_post(postid, 'blog')
                logger.info("Incremental site regeneration completed")
            except Exception as e:
                logger.error(f"Incremental site regeneration failed: {e}")
                # Don't raise - post was still edited successfully
        
        logger.info("blogger_editPost completed successfully")
        return True
    
    def blogger_deletePost(self, appkey: str, postid: str, username: str, password: str,
                          publish: bool) -> bool:
        """Delete a blog post."""
        logger.info(f"blogger_deletePost called: postid={postid}, username={username}, publish={publish}")
        
        if not self._authenticate(username, password):
            logger.error("Authentication failed for deletePost")
            raise Exception("Authentication failed")
        
        file_path = self.blog_dir / postid
        logger.info(f"Deleting post at: {file_path}")
        if not file_path.exists():
            logger.error(f"Post not found: {file_path}")
            raise Exception("Post not found")
        
        try:
            file_path.unlink()
            logger.info(f"Post deleted successfully: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete post: {e}")
            raise
        
        # Regenerate site if published
        if publish:
            logger.info("Incremental site regeneration after post deletion")
            try:
                generator = SiteGenerator()
                generator.incremental_regenerate_after_deletion(postid, 'blog')
                logger.info("Incremental site regeneration completed")
            except Exception as e:
                logger.error(f"Incremental site regeneration failed: {e}")
                # Don't raise - post was still deleted successfully
        
        logger.info("blogger_deletePost completed successfully")
        return True
    
    def blogger_getRecentPosts(self, appkey: str, blogid: str, username: str, password: str,
                              numberOfPosts: int) -> list:
        """Get recent blog posts."""
        logger.info(f"blogger_getRecentPosts called: blogid={blogid}, username={username}, numberOfPosts={numberOfPosts}")
        
        if not self._authenticate(username, password):
            logger.error("Authentication failed for getRecentPosts")
            raise Exception("Authentication failed")
        
        posts = []
        md_files = list(self.blog_dir.glob("*.md"))
        logger.info(f"Found {len(md_files)} markdown files in {self.blog_dir}")
        
        for md_file in sorted(md_files, reverse=True)[:numberOfPosts]:
            try:
                logger.debug(f"Processing file: {md_file}")
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                
                post_data = {
                    'postid': md_file.name,
                    'title': post.metadata.get('title', 'Untitled'),
                    'content': post.content,
                    'dateCreated': post.metadata.get('date', ''),
                    'userid': username
                }
                posts.append(post_data)
                logger.debug(f"Added post: {post_data['title']}")
            except Exception as e:
                logger.warning(f"Failed to process file {md_file}: {e}")
                continue
        
        logger.info(f"Returning {len(posts)} posts")
        return posts
    
    def blogger_getUsersBlogs(self, appkey: str, username: str, password: str) -> list:
        """Get user's blogs."""
        logger.info(f"blogger_getUsersBlogs called: username={username}")
        
        if not self._authenticate(username, password):
            logger.error("Authentication failed for getUsersBlogs")
            raise Exception("Authentication failed")
        
        blogs = [{
            'blogid': 'salasblog2',
            'blogName': 'Salas Blog',
            'url': '/'
        }]
        logger.info(f"Returning {len(blogs)} blogs")
        return blogs
    
    def blogger_getPost(self, appkey: str, postid: str, username: str, password: str) -> dict:
        """Get a specific blog post."""
        logger.info(f"blogger_getPost called: postid={postid}, username={username}")
        
        if not self._authenticate(username, password):
            logger.error("Authentication failed for getPost")
            raise Exception("Authentication failed")
        
        file_path = self.blog_dir / postid
        logger.info(f"Getting post at: {file_path}")
        if not file_path.exists():
            logger.error(f"Post not found: {file_path}")
            raise Exception("Post not found")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            
            post_data = {
                'postid': postid,
                'title': post.metadata.get('title', 'Untitled'),
                'content': post.content,
                'dateCreated': post.metadata.get('date', ''),
                'userid': username
            }
            logger.info(f"Retrieved post: {post_data['title']}")
            return post_data
        except Exception as e:
            logger.error(f"Failed to read post {postid}: {e}")
            raise
    
    def _authenticate(self, username: str, password: str) -> bool:
        """Basic authentication check."""
        import os
        
        logger.debug(f"Authenticating user: {username}")
        
        # Check environment variables for credentials
        expected_username = os.getenv('BLOG_USERNAME', 'admin')
        expected_password = os.getenv('BLOG_PASSWORD', 'password')
        
        logger.debug(f"Expected username: {expected_username}")
        
        # Allow the configured credentials
        if username == expected_username and password == expected_password:
            logger.info("Authentication successful with configured credentials")
            return True
            
        # Fallback: allow any non-empty credentials for development
        fallback_auth = bool(username and password)
        if fallback_auth:
            logger.info("Authentication successful with fallback (development mode)")
        else:
            logger.warning("Authentication failed: empty credentials")
        return fallback_auth