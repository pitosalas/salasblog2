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


class SiteGenerator:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.content_dir = self.root_dir / "content"
        self.blog_dir = self.content_dir / "blog"
        self.raindrops_dir = self.content_dir / "raindrops"
        self.output_dir = self.root_dir / "output"
        self.templates_dir = self.root_dir / "templates"
        self.static_dir = self.root_dir / "static"
        
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
        
        # TODO: Process blog posts from content/blog/
        # TODO: Process raindrops from content/raindrops/
        # TODO: Generate templates
        # TODO: Create search.json
        
        print("✓ Site generated successfully")
    
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