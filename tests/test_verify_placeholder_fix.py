"""
Test to verify that the placeholder title fix will make frontmatter issues obvious.
This test shows what the live server should look like after deploying the fix.
"""

import pytest
import tempfile
from pathlib import Path
from salasblog2.generator import SiteGenerator


def test_simulate_live_server_frontmatter_issue():
    """Simulate what the live server issue would look like with our fix."""
    # Create a temporary directory
    test_dir = Path(tempfile.mkdtemp())
    content_dir = test_dir / "content"
    pages_dir = content_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    
    # Simulate the problematic about.md file (frontmatter parsing fails)
    about_file = pages_dir / "about.md"
    about_file.write_text("""This looks like the about.md file has malformed frontmatter
or no frontmatter at all, which causes the parser to fail and fall back
to the filename.""")
    
    # Simulate working files (like brandeis.md)
    brandeis_file = pages_dir / "brandeis.md"
    brandeis_file.write_text("""---
title: "Brandeis University"
date: "2024-01-01"
category: "Education"
---
Information about Brandeis University.""")
    
    curacao_file = pages_dir / "curacao.md"
    curacao_file.write_text("""---
title: "Curacao"
date: "2024-01-01"
category: "Travel"
---
Information about Curacao.""")
    
    # Test with our generator
    generator = SiteGenerator(theme="test")
    generator.pages_dir = pages_dir
    
    pages = generator.load_posts('pages')
    
    print("\n=== SIMULATION: What live server would show after fix ===")
    for page in sorted(pages, key=lambda p: p['filename']):
        title = page['title']
        filename = page['filename']
        
        if title.startswith('placeholder title:'):
            print(f"🔴 NEEDS FIXING: '{title}' (file: {filename}.md)")
        else:
            print(f"✅ WORKING: '{title}' (file: {filename}.md)")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    
    # Verify that about.md would show placeholder
    about_page = next(p for p in pages if p['filename'] == 'about')
    assert about_page['title'] == "placeholder title: About"
    
    # Verify that working files still work
    brandeis_page = next(p for p in pages if p['filename'] == 'brandeis')
    assert brandeis_page['title'] == "Brandeis University"
    
    curacao_page = next(p for p in pages if p['filename'] == 'curacao')
    assert curacao_page['title'] == "Curacao"


if __name__ == "__main__":
    test_simulate_live_server_frontmatter_issue()