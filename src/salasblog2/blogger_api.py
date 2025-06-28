"""
Blogger API (XML-RPC) implementation for Salasblog2
Supports Blogger API methods for compatibility with blog editors like Windows Live Writer and MarsEdit.
Uses hybrid approach: immediate file operations + deferred Git sync for better performance.
"""
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import frontmatter
import re
import logging
import os
from .generator import SiteGenerator
from .git_sync import get_git_sync_service
from .utils import create_filename_from_title

# Set up logging
logger = logging.getLogger(__name__)


class BloggerAPI:
    """Blogger API implementation for XML-RPC compatibility with blog editors."""
    
    def __init__(self):
        self.root_dir = Path.cwd()
        self.blog_dir = self.root_dir / "content" / "blog"
        self.blog_dir.mkdir(parents=True, exist_ok=True)
        self.git_sync_service = get_git_sync_service()
        logger.info(f"BloggerAPI initialized with hybrid Git sync, blog_dir: {self.blog_dir}")
    
    def _parse_content(self, content: str) -> tuple[str, str]:
        """Parse blog content to extract title and body."""
        lines = content.strip().split('\n')
        title = lines[0] if lines else "Untitled Post"
        body_content = '\n'.join(lines[1:]) if len(lines) > 1 else content
        return title, body_content
    
    def _create_post_frontmatter(self, title: str, body_content: str) -> frontmatter.Post:
        """Create frontmatter post object with standard metadata."""
        post = frontmatter.Post(body_content)
        post.metadata = {
            'title': title,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'type': 'blog',
            'category': 'General'
        }
        return post
    
    def _write_post_file(self, file_path: Path, post: frontmatter.Post):
        """Write post to file with explicit flush to ensure immediate availability."""
        logger.info(f"Writing post to: {file_path}")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
                f.flush()  # Force OS buffer flush
                os.fsync(f.fileno())  # Force disk write
            logger.info(f"Post written and flushed to disk: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write post: {e}")
            raise
    
    def _regenerate_and_verify(self, filename: str, operation: str):
        """Handle site regeneration and file verification for create/edit operations."""
        if operation.lower() == "delete":
            logger.info("Incremental site regeneration after post deletion")
            generator = SiteGenerator()
            generator.incremental_regenerate_after_deletion(filename, 'blog')
            logger.info("Incremental site regeneration completed")
            
            # Verify files for deletion
            filename_stem = filename.replace('.md', '')
            expected_files = [
                generator.output_dir / "blog" / "index.html",            # Blog listing
                generator.output_dir / "index.html",                     # Home page
                generator.output_dir / "search.json"                     # Search index
            ]
            
            # Verify expected files exist
            for expected_file in expected_files:
                if not expected_file.exists():
                    logger.error(f"Expected generated file not found: {expected_file}")
                    raise Exception(f"Generated file missing: {expected_file}")
            
            # Verify individual post file was removed
            deleted_file = generator.output_dir / "blog" / f"{filename_stem}.html"
            if deleted_file.exists():
                logger.error(f"Expected deleted file still exists: {deleted_file}")
                raise Exception(f"Deleted file still present: {deleted_file}")
            
            logger.info("All expected files verified after incremental deletion regeneration")
            
        else:
            # Handle create/edit operations
            operation_name = "creation" if operation.lower() == "create" else "edit"
            logger.info(f"Incremental site regeneration after post {operation_name}")
            
            generator = SiteGenerator()
            generator.incremental_regenerate_post(filename, 'blog')
            logger.info("Incremental site regeneration completed")
            
            # Verify generated files exist before returning
            filename_stem = filename.replace('.md', '')
            expected_files = [
                generator.output_dir / "blog" / f"{filename_stem}.html",  # Individual post
                generator.output_dir / "blog" / "index.html",            # Blog listing
                generator.output_dir / "index.html",                     # Home page
                generator.output_dir / "search.json"                     # Search index
            ]
            
            for expected_file in expected_files:
                if not expected_file.exists():
                    logger.error(f"Expected generated file not found: {expected_file}")
                    raise Exception(f"Generated file missing: {expected_file}")
            
            logger.info("All expected files verified after incremental regeneration")
    
    def _queue_git_sync(self, operation: str, filename: str):
        """Queue Git operation for async processing."""
        logger.info(f"Queueing Git sync for {operation}d post")
        self.git_sync_service.queue_operation(operation, filename)
    
    def _authenticate_or_raise(self, username: str, password: str):
        """Authenticate user or raise exception."""
        if not self._authenticate(username, password):
            logger.error("Authentication failed")
            raise Exception("Authentication failed")
    
    
    
    def blogger_newPost(self, appkey: str, blogid: str, username: str, password: str, 
                       content: str, publish: bool) -> str:
        """Create a new blog post and return the post ID (filename)."""
        logger.info(f"blogger_newPost called: appkey={appkey}, blogid={blogid}, username={username}, publish={publish}")
        
        # Authenticate user
        self._authenticate_or_raise(username, password)
        
        # Parse content and create post
        title, body_content = self._parse_content(content)
        logger.info(f"Parsed title: '{title}', body length: {len(body_content)}")
        
        filename = create_filename_from_title(title)
        logger.info(f"Generated filename: {filename}")
        
        post = self._create_post_frontmatter(title, body_content)
        file_path = self.blog_dir / filename
        self._write_post_file(file_path, post)
        
        # Handle publishing workflow
        if publish:
            try:
                self._regenerate_and_verify(filename, "create")
            except Exception as e:
                logger.error(f"Incremental site regeneration failed: {e}")
                # Don't raise - post was still created successfully
            
            self._queue_git_sync("create", filename)
        
        logger.info(f"blogger_newPost completed successfully, returning: {filename}")
        return filename
    
    def blogger_editPost(self, appkey: str, postid: str, username: str, password: str,
                        content: str, publish: bool) -> bool:
        """Edit an existing blog post."""
        logger.info(f"blogger_editPost called: postid={postid}, username={username}, publish={publish}")
        
        # Authenticate user
        self._authenticate_or_raise(username, password)
        
        # Verify post exists
        file_path = self.blog_dir / postid
        logger.info(f"Editing post at: {file_path}")
        if not file_path.exists():
            logger.error(f"Post not found: {file_path}")
            raise Exception("Post not found")
        
        # Parse content and update post
        title, body_content = self._parse_content(content)
        post = self._create_post_frontmatter(title, body_content)
        self._write_post_file(file_path, post)
        
        # Handle publishing workflow
        if publish:
            try:
                self._regenerate_and_verify(postid, "edit")
            except Exception as e:
                logger.error(f"Incremental site regeneration failed: {e}")
                # Don't raise - post was still edited successfully
            
            self._queue_git_sync("edit", postid)
        
        logger.info("blogger_editPost completed successfully")
        return True
    
    def blogger_deletePost(self, appkey: str, postid: str, username: str, password: str,
                          publish: bool) -> bool:
        """Delete a blog post."""
        logger.info(f"blogger_deletePost called: postid={postid}, username={username}, publish={publish}")
        
        # Authenticate user
        self._authenticate_or_raise(username, password)
        
        # Verify post exists and delete it
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
        
        # Handle publishing workflow
        if publish:
            try:
                self._regenerate_and_verify(postid, "delete")
            except Exception as e:
                logger.error(f"Incremental site regeneration failed: {e}")
                # Don't raise - post was still deleted successfully
            
            self._queue_git_sync("delete", postid)
        
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
        # Check environment variables for credentials
        expected_username = os.getenv('BLOG_USERNAME', 'admin')
        expected_password = os.getenv('BLOG_PASSWORD', 'password')
        
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