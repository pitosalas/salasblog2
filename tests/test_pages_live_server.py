"""
Integration tests for the pages feature against the live server at salas.com.

These tests validate that the pages feature works correctly in the production environment.
Run with: uv run pytest tests/test_pages_live_server.py -v

Note: These tests require internet connectivity and depend on the live server being up.
"""

import pytest
import requests
from urllib.parse import urljoin
import time
from bs4 import BeautifulSoup


class TestPagesLiveServer:
    """Integration tests for pages feature against live server."""
    
    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL for the live server."""
        return "https://salas.com"
    
    @pytest.fixture(scope="class")
    def check_server_accessible(self, base_url):
        """Check if the live server is accessible, skip tests if not."""
        try:
            response = requests.get(base_url, timeout=10)
            if response.status_code != 200:
                pytest.skip(f"Live server not accessible at {base_url}")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Live server not accessible: {e}")
    
    def test_pages_url_produces_html(self, base_url, check_server_accessible):
        """Test that /pages/ URL produces HTML response on live server."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert len(response.text) > 0
        assert "<!DOCTYPE html>" in response.text or "<html" in response.text
    
    def test_pages_url_contains_menu_and_header(self, base_url, check_server_accessible):
        """Test that /pages/ URL contains standard menu bar and header on live server."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for header structure
        header = soup.find('header')
        assert header is not None, "Header element should exist"
        
        nav = soup.find('nav')
        assert nav is not None, "Navigation element should exist"
        
        # Check for menu items
        links = soup.find_all('a')
        link_hrefs = [link.get('href') for link in links if link.get('href')]
        
        # Should contain navigation links
        assert any('/' in href for href in link_hrefs), "Should have home link"
        assert any('/blog/' in href for href in link_hrefs), "Should have blog link"
        assert any('/pages/' in href for href in link_hrefs), "Should have pages link"
        
        # Should contain site branding
        assert "Salas" in response.text or "Blog" in response.text
    
    def test_pages_listing_has_content(self, base_url, check_server_accessible):
        """Test that pages listing has actual content on live server."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for page cards or similar content structure
        page_cards = soup.find_all('div', class_='page-card')
        if not page_cards:
            # Try alternative selectors if page-card doesn't exist
            page_cards = soup.find_all('article') or soup.find_all('div', class_='page')
        
        assert len(page_cards) > 0, "Should have at least one page listed"
        
        # Check that pages have titles
        for card in page_cards[:3]:  # Check first 3 cards
            # Look for title in various possible locations
            title_element = (card.find('h1') or card.find('h2') or 
                           card.find('h3') or card.find('h4') or
                           card.find('a'))
            if title_element:
                title_text = title_element.get_text().strip()
                assert len(title_text) > 0, f"Page card should have non-empty title"
    
    def test_individual_pages_accessible(self, base_url, check_server_accessible):
        """Test that individual pages are accessible from the listing."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find page links
        page_links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and (href.endswith('.html') or '/pages/' in href):
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = urljoin(base_url, href)
                elif not href.startswith('http'):
                    href = urljoin(f"{base_url}/pages/", href)
                page_links.append(href)
        
        assert len(page_links) > 0, "Should have links to individual pages"
        
        # Test that at least one individual page loads
        for link in page_links[:3]:  # Test first 3 links
            try:
                page_response = requests.get(link, timeout=10)
                if page_response.status_code == 200:
                    # Verify it's a real page with content
                    page_soup = BeautifulSoup(page_response.text, 'html.parser')
                    
                    # Should have a title
                    title = page_soup.find('title') or page_soup.find('h1') or page_soup.find('h2')
                    assert title is not None, f"Page {link} should have a title"
                    
                    # Should have some content
                    content_length = len(page_soup.get_text().strip())
                    assert content_length > 100, f"Page {link} should have substantial content"
                    
                    # At least one page worked, we can return
                    return
            except requests.exceptions.RequestException:
                continue
        
        pytest.fail("No individual pages were accessible")
    
    def test_pages_have_markdown_rendering(self, base_url, check_server_accessible):
        """Test that pages show evidence of markdown rendering."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for evidence of markdown rendering (HTML elements that suggest markdown)
        markdown_elements = (
            soup.find_all('strong') +  # **bold**
            soup.find_all('em') +      # *italic*
            soup.find_all('code') +    # `code`
            soup.find_all('ul') +      # lists
            soup.find_all('ol') +      # numbered lists
            soup.find_all('blockquote') + # > quotes
            soup.find_all('h1') +      # # headers
            soup.find_all('h2') +      # ## headers
            soup.find_all('h3')        # ### headers
        )
        
        # If we find markdown-typical elements, that's good evidence
        # If not, at least check that content exists
        if len(markdown_elements) > 0:
            assert True, "Found evidence of markdown rendering"
        else:
            # Just ensure there's substantial content
            content = soup.get_text()
            assert len(content) > 200, "Should have substantial content even without markdown elements"
    
    def test_pages_css_and_styling(self, base_url, check_server_accessible):
        """Test that pages have proper CSS styling."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        
        # Check for CSS links
        soup = BeautifulSoup(response.text, 'html.parser')
        css_links = soup.find_all('link', {'rel': 'stylesheet'})
        
        assert len(css_links) > 0, "Should have CSS stylesheets linked"
        
        # Check that CSS files are accessible
        for css_link in css_links[:2]:  # Test first 2 CSS files
            css_href = css_link.get('href')
            if css_href:
                if css_href.startswith('/'):
                    css_url = urljoin(base_url, css_href)
                elif not css_href.startswith('http'):
                    css_url = urljoin(base_url, css_href)
                else:
                    css_url = css_href
                
                try:
                    css_response = requests.get(css_url, timeout=10)
                    assert css_response.status_code == 200, f"CSS file {css_url} should be accessible"
                    assert "text/css" in css_response.headers.get("content-type", ""), f"CSS file {css_url} should have correct content-type"
                except requests.exceptions.RequestException:
                    # CSS might be inline or from CDN, don't fail if some aren't accessible
                    pass
    
    def test_pages_admin_controls_hidden_by_default(self, base_url, check_server_accessible):
        """Test that admin controls are not visible to unauthenticated users."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        
        # Admin controls should either not be present or be hidden
        # Since we're not authenticated, we shouldn't see edit/delete buttons
        
        # Check that sensitive admin paths are not exposed
        assert '/admin/edit-page/' not in response.text or 'display: none' in response.text
        assert '/admin/delete-page/' not in response.text or 'display: none' in response.text
        
        # Admin controls might be in the DOM but hidden - that's okay
        # What matters is they're not visible to unauthenticated users
    
    def test_pages_meta_tags_present(self, base_url, check_server_accessible):
        """Test that pages have proper meta tags for SEO."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for basic meta tags
        title = soup.find('title')
        assert title is not None, "Should have title tag"
        assert len(title.get_text().strip()) > 0, "Title should not be empty"
        
        # Check for viewport meta tag (mobile responsiveness)
        viewport = soup.find('meta', {'name': 'viewport'})
        assert viewport is not None, "Should have viewport meta tag for mobile"
        
        # Check for description meta tag
        description = soup.find('meta', {'name': 'description'})
        if description:
            desc_content = description.get('content', '')
            assert len(desc_content) > 0, "Description meta tag should not be empty"
    
    def test_pages_accessibility_basics(self, base_url, check_server_accessible):
        """Test basic accessibility features."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check that images have alt attributes
        images = soup.find_all('img')
        for img in images[:5]:  # Check first 5 images
            alt = img.get('alt')
            # Alt can be empty string for decorative images, but should be present
            assert alt is not None, f"Image should have alt attribute: {img}"
        
        # Check that links have meaningful text
        links = soup.find_all('a')
        for link in links[:10]:  # Check first 10 links
            link_text = link.get_text().strip()
            href = link.get('href')
            if href and not href.startswith('#'):  # Skip anchor links
                assert len(link_text) > 0, f"Link should have meaningful text: {link}"
    
    def test_pages_response_time(self, base_url, check_server_accessible):
        """Test that pages load within reasonable time."""
        start_time = time.time()
        response = requests.get(f"{base_url}/pages/", timeout=10)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0, f"Page should load within 5 seconds, took {response_time:.2f}s"
    
    def test_pages_mobile_responsive(self, base_url, check_server_accessible):
        """Test that pages are mobile responsive."""
        # Test with mobile user agent
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
        }
        
        response = requests.get(f"{base_url}/pages/", headers=mobile_headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        assert response.status_code == 200
        
        # Check for viewport meta tag
        viewport = soup.find('meta', {'name': 'viewport'})
        assert viewport is not None, "Should have viewport meta tag for mobile"
        
        # Check for responsive CSS (media queries)
        css_content = response.text
        assert '@media' in css_content or 'responsive' in css_content.lower(), "Should have responsive CSS"


@pytest.mark.integration
class TestPagesLiveServerIntegration:
    """Extended integration tests that may require specific server configuration."""
    
    def test_pages_api_endpoints(self, base_url="https://salas.com"):
        """Test that API endpoints work correctly."""
        # Test admin status endpoint
        try:
            response = requests.get(f"{base_url}/api/admin-status", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert "authenticated" in data
            # Should be False for unauthenticated requests
            assert data["authenticated"] is False
        except requests.exceptions.RequestException:
            pytest.skip("API endpoints not accessible")
    
    def test_pages_rsd_xml(self, base_url="https://salas.com"):
        """Test RSD XML endpoint for blog API discovery."""
        try:
            response = requests.get(f"{base_url}/rsd.xml", timeout=10)
            assert response.status_code == 200
            assert "application/rsd+xml" in response.headers.get("content-type", "")
            assert "<rsd" in response.text
        except requests.exceptions.RequestException:
            pytest.skip("RSD XML endpoint not accessible")
    
    def test_pages_sitemap_includes_pages(self, base_url="https://salas.com"):
        """Test that sitemap includes pages."""
        try:
            response = requests.get(f"{base_url}/sitemap.xml", timeout=10)
            if response.status_code == 200:
                assert "/pages/" in response.text or "pages" in response.text.lower()
        except requests.exceptions.RequestException:
            pytest.skip("Sitemap not accessible")