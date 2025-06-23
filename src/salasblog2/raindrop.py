"""
Raindrop.io integration for downloading bookmarks and converting to markdown.
"""
import os
import sys
import json
import requests
import yaml
import shutil
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class RaindropDownloader:
    def __init__(self, access_token=None):
        self.access_token = access_token or os.getenv("RAINDROP_TOKEN")
        self.base_url = "https://api.raindrop.io/rest/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        self.drops_dir = Path("content/raindrops")
        self.cache_file = Path(".rd_cache.json")

    def authenticate(self):
        if not self.access_token:
            print("Error: RAINDROP_TOKEN environment variable not set")
            print("Get your token from: https://app.raindrop.io/settings/integrations")
            sys.exit(1)

        response = requests.get(f"{self.base_url}/user", headers=self.headers)
        if response.status_code != 200:
            print(f"Authentication failed: {response.status_code}")
            sys.exit(1)

        print(f"Authenticated as: {response.json()['user']['fullName']}")

    def load_cache(self):
        if self.cache_file.exists():
            with open(self.cache_file, "r") as f:
                return json.load(f)
        return {"downloaded": set()}

    def save_cache(self, cache):
        cache["downloaded"] = list(cache["downloaded"])
        with open(self.cache_file, "w") as f:
            json.dump(cache, f)

    def fetch_raindrops(self, max_items=None):
        all_raindrops = []
        page = 0

        print("Fetching raindrops from all collections...")

        while True:
            # Calculate how many items to fetch this page
            if max_items:
                remaining = max_items - len(all_raindrops)
                if remaining <= 0:
                    break
                perpage = min(50, remaining)
            else:
                perpage = 50

            print(f"  Fetching page {page + 1}...", end=" ")

            response = requests.get(
                f"{self.base_url}/raindrops/0",
                headers=self.headers,
                params={"page": page, "perpage": perpage},
            )

            if response.status_code != 200:
                print(f"\\nFailed to fetch raindrops: {response.status_code}")
                print(f"Response: {response.text}")
                break

            data = response.json()
            raindrops = data.get("items", [])

            if not raindrops:
                print("(no more items)")
                break

            print(f"got {len(raindrops)} items")
            all_raindrops.extend(raindrops)
            page += 1

            # Stop if we have enough items
            if max_items and len(all_raindrops) >= max_items:
                break

        print(f"Total raindrops fetched: {len(all_raindrops)}")
        return all_raindrops

    def create_raindrops_directory(self):
        self.drops_dir.mkdir(exist_ok=True)

    def generate_filename(self, raindrop, counter):
        created = datetime.fromisoformat(raindrop["created"].replace("Z", "+00:00"))
        date_str = created.strftime("%y-%m-%d")

        # Get title and clean it for filename
        title = raindrop.get("title", "Untitled")[:30]
        # Replace characters that aren't filename-safe
        safe_title = "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        safe_title = safe_title.replace(" ", "-")

        return f"{date_str}-{counter}-{safe_title}.md"

    def format_as_markdown(self, raindrop):
        created = datetime.fromisoformat(raindrop["created"].replace("Z", "+00:00"))

        # Format tags as space-separated string to match existing raindrop format
        tags = raindrop.get("tags", [])
        tags_str = " ".join(tags) if tags else ""

        frontmatter = {
            "date": created.isoformat(),
            "excerpt": raindrop.get("excerpt", ""),
            "tags": [tags_str] if tags_str else [],
            "title": raindrop.get("title", "Untitled"),
            "type": "drop", 
            "url": raindrop.get("link", ""),
        }

        yaml_content = yaml.dump(frontmatter, default_flow_style=False)

        content = f"---\\n{yaml_content}---\\n\\n# {raindrop.get('title', 'Untitled')}\\n\\n**URL:** {raindrop.get('link', '')}\\n"

        if raindrop.get("excerpt"):
            content += f"\\n**Excerpt:** {raindrop['excerpt']}\\n"

        if raindrop.get("note"):
            content += f"\\n**Notes:**\\n{raindrop['note']}\\n"

        return content

    def reset_data(self):
        """Delete all raindrops and cache to start fresh"""
        if self.drops_dir.exists():
            print(f"Removing existing raindrops directory: {self.drops_dir}")
            shutil.rmtree(self.drops_dir)

        if self.cache_file.exists():
            print(f"Removing cache file: {self.cache_file}")
            self.cache_file.unlink()

        print("Reset complete - all data cleared")

    def download_raindrops(self, reset=False, count=None):
        self.authenticate()

        if reset:
            self.reset_data()

        self.create_raindrops_directory()

        # Load cache first
        cache = self.load_cache()

        if reset:
            # If reset, fetch only what we need and start with empty cache
            print("Fetching raindrops...")
            raindrops = self.fetch_raindrops(max_items=count)
            new_drops = raindrops
            downloaded_ids = set()  # Start with empty cache
            print(f"Rebuilding {len(new_drops)} raindrops")
        else:
            # Normal mode - fetch more to account for already downloaded items
            print("Fetching raindrops...")
            fetch_limit = (
                count * 3 if count else None
            )  # Fetch extra to account for duplicates
            raindrops = self.fetch_raindrops(max_items=fetch_limit)

            downloaded_ids = set(cache["downloaded"])
            new_drops = [r for r in raindrops if str(r["_id"]) not in downloaded_ids]

            if not new_drops:
                print("No new raindrops to download")
                return

            print(f"Found {len(new_drops)} new raindrops")

            # Limit the number of drops if count is specified
            if count is not None and count > 0:
                new_drops = new_drops[:count]
                print(f"Limiting to first {len(new_drops)} raindrops")

        counter = 1
        for i, raindrop in enumerate(new_drops, 1):
            filename = self.generate_filename(raindrop, counter)
            filepath = self.drops_dir / filename

            print(
                f"  [{i}/{len(new_drops)}] Writing: {filename} - {raindrop.get('title', 'Untitled')[:50]}..."
            )

            markdown_content = self.format_as_markdown(raindrop)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            downloaded_ids.add(str(raindrop["_id"]))
            counter += 1

        cache["downloaded"] = downloaded_ids
        self.save_cache(cache)

        print(f"Downloaded {len(new_drops)} raindrops to {self.drops_dir}")