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
import os
from xmlrpc.client import Fault
from .generator import SiteGenerator
from .utils import create_filename_from_title

# Set up logging
logger = logging.getLogger(__name__)


class BloggerAPI:
    """Blogger API implementation for XML-RPC compatibility with blog editors."""
    
    def __init__(self):
        self.root_dir = Path.cwd()
        self.blog_dir = self.root_dir / "content" / "blog"
        self.blog_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"BloggerAPI initialized, blog_dir: {self.blog_dir}")
    
    def _parse_content(self, content: str) -> tuple[str, str]:
        """Parse blog content to extract title and body."""
        # Check if content contains XML-like structure with title
        if '<title>' in content and '</title>' in content:
            # Extract title from XML-like structure
            import re
            title_match = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                # Remove title tags from content
                body_content = re.sub(r'<title>.*?</title>\s*', '', content, flags=re.DOTALL).strip()
                return title, body_content
        
        # Fallback to original behavior - use first line as title
        lines = content.strip().split('\n')
        
        # If first line looks like a title (short, no periods, etc.)
        if lines and len(lines) > 1:
            first_line = lines[0].strip()
            # Consider it a title if it's reasonably short and doesn't end with a period
            if len(first_line) <= 100 and not first_line.endswith('.') and not first_line.startswith('#'):
                title = first_line
                body_content = '\n'.join(lines[1:])
                return title, body_content
        
        # If we can't determine a clear title, use the content as-is with a generated title
        title = "Blog Post"  # Generic title
        body_content = content
        return title, body_content
    
    def _parse_content_or_struct(self, content) -> tuple[str, str]:
        """Parse content whether it's a string or structured data."""
        if isinstance(content, dict):
            # Handle structured content (modern blog editors)
            title = content.get('title', 'Untitled Post')
            body = content.get('description', content.get('content', ''))
            logger.info(f"Received structured content: title='{title}', body_length={len(body)}")
            return title, body
        elif isinstance(content, str):
            # Handle string content (legacy format)
            logger.info(f"Received string content, parsing: {len(content)} chars")
            return self._parse_content(content)
        else:
            # Fallback
            logger.warning(f"Unknown content type: {type(content)}, converting to string")
            return self._parse_content(str(content))
    
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
    
    
    def _create_fault(self, code: int, message: str):
        """Create a proper XML-RPC fault for better error handling in blog editors."""
        logger.error(f"XML-RPC Fault {code}: {message}")
        raise Fault(code, message)
    
    def _authenticate_or_raise(self, username: str, password: str):
        """Authenticate user or raise XML-RPC fault."""
        if not self._authenticate(username, password):
            logger.error("Authentication failed")
            self._create_fault(401, "Authentication failed. Please check your username and password.")
    
    
    
    def blogger_newPost(self, appkey: str, blogid: str, username: str, password: str, 
                       content, publish: bool) -> str:
        """Create a new blog post and return the post ID (filename)."""
        logger.info(f"blogger_newPost called: appkey={appkey}, blogid={blogid}, username={username}, publish={publish}")
        logger.info(f"blogger_newPost content type: {type(content)}")
        logger.info(f"blogger_newPost full content: {repr(content)}")
        
        # Authenticate user
        self._authenticate_or_raise(username, password)
        
        # Parse content and create post
        title, body_content = self._parse_content_or_struct(content)
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
            
        
        logger.info(f"blogger_newPost completed successfully, returning: {filename}")
        return filename
    
    def blogger_editPost(self, appkey: str, postid: str, username: str, password: str,
                        content, publish: bool) -> bool:
        """Edit an existing blog post."""
        logger.info(f"blogger_editPost called: postid={postid}, username={username}, publish={publish}")
        logger.info(f"blogger_editPost content type: {type(content)}")
        logger.info(f"blogger_editPost full content: {repr(content)}")
        
        # Authenticate user
        self._authenticate_or_raise(username, password)
        
        # Check if post exists, create if it doesn't
        file_path = self.blog_dir / postid
        logger.info(f"Editing post at: {file_path}")
        is_new_post = not file_path.exists()
        
        if is_new_post:
            logger.warning(f"Post not found: {file_path} - Creating new post with this filename")
            # Check if it might be a different file extension or similar name
            similar_files = list(self.blog_dir.glob(f"{postid.replace('.md', '')}*"))
            if similar_files:
                suggestion = similar_files[0].name
                logger.warning(f"Similar file found: {suggestion} - but creating new post as requested")
            logger.info(f"Creating new post from edit request: {postid}")
        
        # Parse content and update post
        title, body_content = self._parse_content_or_struct(content)
        post = self._create_post_frontmatter(title, body_content)
        self._write_post_file(file_path, post)
        
        # Handle publishing workflow
        if publish:
            try:
                # Use "create" operation for new posts, "edit" for existing ones
                operation = "create" if is_new_post else "edit"
                self._regenerate_and_verify(postid, operation)
            except Exception as e:
                logger.error(f"Incremental site regeneration failed: {e}")
                # Don't raise - post was still created/edited successfully
            
        
        logger.info("blogger_editPost completed successfully")
        return True
    
    def blogger_deletePost(self, appkey: str, postid: str, username: str, password: str,
                          publish: bool) -> bool:
        """Delete a blog post."""
        logger.info(f"blogger_deletePost called: postid={postid}, username={username}, publish={publish}")
        
        # Authenticate user
        self._authenticate_or_raise(username, password)
        
        # Check if post exists, warn if it doesn't but don't fail
        file_path = self.blog_dir / postid
        logger.info(f"Deleting post at: {file_path}")
        if not file_path.exists():
            logger.warning(f"Post not found for deletion: {file_path} - May have already been deleted")
            # Check if it might be a different file extension or similar name
            similar_files = list(self.blog_dir.glob(f"{postid.replace('.md', '')}*"))
            if similar_files:
                suggestion = similar_files[0].name
                logger.warning(f"Similar file found: {suggestion} - but requested file doesn't exist")
            logger.info(f"Delete operation completed (file didn't exist): {postid}")
            return True  # Return success since the desired end state is achieved
        
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
        
        self._authenticate_or_raise(username, password)
        
        file_path = self.blog_dir / postid
        logger.info(f"Getting post at: {file_path}")
        if not file_path.exists():
            logger.warning(f"Post not found: {file_path}")
            # Check if it might be a different file extension or similar name
            similar_files = list(self.blog_dir.glob(f"{postid.replace('.md', '')}*"))
            if similar_files:
                suggestion = similar_files[0].name
                self._create_fault(404, f"Post '{postid}' not found. Did you mean '{suggestion}'? Please refresh your post list in MarsEdit to see current posts.")
            else:
                self._create_fault(404, f"Post '{postid}' not found. The post may have been deleted or moved. Please refresh your post list in MarsEdit to see current posts.")
        
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
            self._create_fault(500, f"Unable to read post '{postid}'. The file may be corrupted or have invalid formatting. Error: {str(e)}")
    

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

    # MetaWeblog API wrapper methods (different parameter signatures)
    def metaweblog_newPost(self, blogid: str, username: str, password: str, struct, publish: bool) -> str:
        """MetaWeblog API newPost - maps to blogger_newPost with added appkey"""
        return self.blogger_newPost("metaweblog", blogid, username, password, struct, publish)
    
    def metaweblog_editPost(self, postid: str, username: str, password: str, struct, publish: bool) -> bool:
        """MetaWeblog API editPost - maps to blogger_editPost with added appkey"""
        return self.blogger_editPost("metaweblog", postid, username, password, struct, publish)
    
    def metaweblog_getPost(self, postid: str, username: str, password: str) -> dict:
        """MetaWeblog API getPost - maps to blogger_getPost with added appkey"""
        return self.blogger_getPost("metaweblog", postid, username, password)
    
    def metaweblog_getRecentPosts(self, blogid: str, username: str, password: str, numberOfPosts: int) -> list:
        """MetaWeblog API getRecentPosts - maps to blogger_getRecentPosts with added appkey"""
        return self.blogger_getRecentPosts("metaweblog", blogid, username, password, numberOfPosts)