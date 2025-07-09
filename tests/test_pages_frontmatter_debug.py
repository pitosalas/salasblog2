"""
Debug tests to investigate frontmatter parsing issues on the live server.
These tests help identify why page titles aren't coming from frontmatter.
"""

import pytest
import requests
from bs4 import BeautifulSoup
import re


class TestPagesFrontmatterDebug:
    """Debug tests for frontmatter parsing issues."""
    
    @pytest.fixture(scope="class")
    def base_url(self):
        return "https://salas.com"
    
    def test_debug_pages_listing_titles(self, base_url):
        """Debug what titles are actually being displayed in the pages listing."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("\n=== DEBUG: Pages Listing Titles ===")
        
        # Find all possible title elements
        title_elements = []
        
        # Look for page cards
        page_cards = soup.find_all('div', class_='page-card')
        if page_cards:
            print(f"Found {len(page_cards)} page cards")
            for i, card in enumerate(page_cards):
                # Look for titles in various elements
                title_elem = card.find('h3') or card.find('h2') or card.find('h1')
                if title_elem:
                    title_text = title_elem.get_text().strip()
                    link = title_elem.find('a')
                    link_href = link.get('href') if link else None
                    print(f"  Card {i+1}: '{title_text}' -> {link_href}")
                    title_elements.append((title_text, link_href))
        else:
            # Fallback: look for any links that might be page titles
            links = soup.find_all('a')
            for link in links:
                href = link.get('href', '')
                if '.html' in href and '/pages/' not in href and href.startswith('/'):
                    title_text = link.get_text().strip()
                    if title_text and len(title_text) > 1:
                        print(f"  Link: '{title_text}' -> {href}")
                        title_elements.append((title_text, href))
        
        # Print raw HTML for debugging
        print(f"\n=== DEBUG: Raw HTML Sample ===")
        print(response.text[:2000] + "..." if len(response.text) > 2000 else response.text)
        
        assert len(title_elements) > 0, "Should find some page titles"
        return title_elements
    
    def test_debug_individual_page_frontmatter(self, base_url):
        """Debug an individual page to see if frontmatter is being used."""
        # Try to access the about page directly
        test_pages = [
            "/about.html",
            "/about/",
            "/pages/about.html",
            "/contact.html",
            "/contact/"
        ]
        
        for page_path in test_pages:
            try:
                response = requests.get(f"{base_url}{page_path}", timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    print(f"\n=== DEBUG: {page_path} ===")
                    
                    # Check page title
                    page_title = soup.find('title')
                    if page_title:
                        print(f"HTML Title: '{page_title.get_text().strip()}'")
                    
                    # Check main heading
                    main_heading = soup.find('h1')
                    if main_heading:
                        print(f"Main Heading: '{main_heading.get_text().strip()}'")
                    
                    # Look for any evidence of frontmatter data
                    content = response.text
                    
                    # Check if we can see any frontmatter remnants or metadata
                    if 'title:' in content.lower():
                        print("Found 'title:' in content - might be visible frontmatter")
                    
                    if 'date:' in content.lower():
                        print("Found 'date:' in content - might be visible frontmatter")
                    
                    if '---' in content:
                        print("Found '---' in content - might be frontmatter delimiters")
                    
                    # Check for category information
                    if 'category' in content.lower():
                        print("Found 'category' in content")
                    
                    # Sample of the content
                    text_content = soup.get_text()
                    print(f"Content sample: {text_content[:200]}...")
                    
                    break
            except requests.exceptions.RequestException:
                continue
    
    def test_debug_compare_expected_vs_actual_titles(self, base_url):
        """Compare what we expect vs what we actually see."""
        # What we expect based on our test data
        expected_titles = {
            "about": "About Me",
            "contact": "Contact Information", 
            "projects": "My Projects"
        }
        
        # Get actual titles from pages listing
        response = requests.get(f"{base_url}/pages/", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"\n=== DEBUG: Expected vs Actual Titles ===")
        
        # Find all page links and their titles
        actual_titles = {}
        
        # Look in page cards
        page_cards = soup.find_all('div', class_='page-card')
        for card in page_cards:
            title_elem = card.find('h3') or card.find('h2') or card.find('h1')
            if title_elem:
                link = title_elem.find('a')
                if link:
                    href = link.get('href', '')
                    title_text = title_elem.get_text().strip()
                    
                    # Extract page name from URL
                    page_name = href.replace('.html', '').replace('/', '').replace('pages', '')
                    if page_name:
                        actual_titles[page_name] = title_text
                        print(f"  {page_name}: Expected='{expected_titles.get(page_name, 'Unknown')}', Actual='{title_text}'")
        
        # If no page cards, look for direct links
        if not actual_titles:
            links = soup.find_all('a')
            for link in links:
                href = link.get('href', '')
                if '.html' in href and href.startswith('/'):
                    title_text = link.get_text().strip()
                    page_name = href.replace('.html', '').replace('/', '')
                    if page_name and title_text and len(title_text) > 1:
                        actual_titles[page_name] = title_text
                        print(f"  {page_name}: Expected='{expected_titles.get(page_name, 'Unknown')}', Actual='{title_text}'")
        
        return actual_titles
    
    def test_debug_check_source_files_format(self, base_url):
        """Try to access raw markdown files if they're exposed (they shouldn't be)."""
        print(f"\n=== DEBUG: Checking for Exposed Source Files ===")
        
        # These should NOT be accessible, but let's check
        source_paths = [
            "/content/pages/about.md",
            "/pages/about.md", 
            "/about.md",
            "/content/about.md"
        ]
        
        for path in source_paths:
            try:
                response = requests.get(f"{base_url}{path}", timeout=5)
                if response.status_code == 200:
                    print(f"WARNING: Source file exposed at {path}")
                    content = response.text[:500]
                    print(f"Content preview: {content}")
                    
                    # Check frontmatter format
                    if content.startswith('---'):
                        print("✓ Proper frontmatter format detected")
                        lines = content.split('\n')
                        for line in lines[:10]:
                            if 'title:' in line:
                                print(f"  Title line: {line}")
                    else:
                        print("✗ No frontmatter detected")
                else:
                    print(f"✓ {path} properly not accessible ({response.status_code})")
            except requests.exceptions.RequestException:
                print(f"✓ {path} not accessible (connection error)")
    
    def test_debug_analyze_page_generation(self, base_url):
        """Analyze how pages are being generated by looking at patterns."""
        response = requests.get(f"{base_url}/pages/", timeout=10)
        content = response.text
        
        print(f"\n=== DEBUG: Page Generation Analysis ===")
        
        # Check for generator metadata
        soup = BeautifulSoup(content, 'html.parser')
        generator_meta = soup.find('meta', {'name': 'generator'})
        if generator_meta:
            print(f"Generator: {generator_meta.get('content')}")
        
        # Check for any comments that might indicate the system
        comments = re.findall(r'<!--(.*?)-->', content, re.DOTALL)
        for comment in comments[:3]:
            if comment.strip():
                print(f"HTML Comment: {comment.strip()}")
        
        # Look for patterns that might indicate frontmatter issues
        if 'filename' in content.lower():
            print("Found 'filename' in content - might be using filename as title")
        
        # Check for any visible frontmatter
        if content.count('---') >= 2:
            print(f"Found {content.count('---')} '---' markers - might be visible frontmatter")
        
        # Check if titles look like filenames
        page_cards = soup.find_all('div', class_='page-card')
        for card in page_cards:
            title_elem = card.find('h3') or card.find('h2') or card.find('h1')
            if title_elem:
                title_text = title_elem.get_text().strip()
                if title_text.lower() in ['about', 'contact', 'projects', 'index']:
                    print(f"Title '{title_text}' looks like a filename - possible frontmatter parsing issue")
        
        return content