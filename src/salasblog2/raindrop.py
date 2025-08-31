"""
Raindrop.io integration for downloading bookmarks and converting to markdown.
"""
import os
import sys
import json
import requests
import shutil
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from .utils import generate_raindrop_filename, format_raindrop_as_markdown

# Constants
DEFAULT_PAGE_SIZE = 50  # Items per page when fetching from Raindrop.io API
DEFAULT_FIRST_SYNC_LIMIT = 100  # Default number of items to fetch on first sync
FETCH_MULTIPLIER = 2  # Multiplier for fetch limit when count is specified on first sync (fetches extra to account for duplicates)

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
        self.drops_dir = Path("/data/content/raindrops")
        self.cache_file = Path("/data/content/.rd_cache.json")

    def authenticate(self):
        """Authenticate with Raindrop.io API."""
        if not self.access_token:
            raise Exception("RAINDROP_TOKEN environment variable not set. Get your token from: https://app.raindrop.io/settings/integrations")

        response = requests.get(f"{self.base_url}/user", headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.status_code}")

        print(f"Authenticated as: {response.json()['user']['fullName']}")

    def load_cache(self):
        # Always try to load from cache file first to get downloaded IDs
        downloaded_ids = set()
        cache_timestamp = None
        
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    cache = json.load(f)
                    downloaded_ids = set(cache.get("downloaded", []))
                    cache_timestamp = cache.get("last_sync_timestamp")
                    print(f"Loaded cache with {len(downloaded_ids)} downloaded IDs")
            except Exception as e:
                print(f"Error loading cache file: {e}")
        
        # Environment variable can override timestamp but not downloaded IDs
        env_timestamp = os.getenv("RAINDROP_LAST_SYNC")
        if env_timestamp and env_timestamp != cache_timestamp:
            print(f"Using environment timestamp: {env_timestamp} (overriding cache: {cache_timestamp})")
            cache_timestamp = env_timestamp
        elif cache_timestamp:
            print(f"Using cached timestamp: {cache_timestamp}")
            
        return {"last_sync_timestamp": cache_timestamp, "downloaded": downloaded_ids}

    def save_cache(self, cache):
        # Create a copy for serialization
        cache_copy = cache.copy()
        cache_copy["downloaded"] = list(cache_copy["downloaded"])
        with open(self.cache_file, "w") as f:
            json.dump(cache_copy, f, indent=2)
        
        # Also save timestamp to environment for backup
        if cache.get("last_sync_timestamp"):
            print(f"Cache saved - next sync will fetch raindrops newer than {cache['last_sync_timestamp']}")

    def rebuild_cache_from_files(self):
        """Rebuild cache by scanning existing markdown files for raindrop IDs."""
        print("Rebuilding cache from existing files...")
        downloaded_ids = set()
        
        if self.drops_dir.exists():
            for md_file in self.drops_dir.glob("*.md"):
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Look for raindrop ID in frontmatter
                        if 'raindrop_id:' in content:
                            for line in content.split('\n'):
                                if line.strip().startswith('raindrop_id:'):
                                    raindrop_id = line.split(':', 1)[1].strip().strip('"\'')
                                    if raindrop_id:
                                        downloaded_ids.add(raindrop_id)
                                    break
                except Exception as e:
                    print(f"Error reading {md_file}: {e}")
        
        print(f"Found {len(downloaded_ids)} raindrop IDs from existing files")
        
        # Update cache with found IDs
        cache = self.load_cache()
        cache["downloaded"] = downloaded_ids
        self.save_cache(cache)
        
        return downloaded_ids

    def _fetch_page(self, page, perpage, since_timestamp=None):
        """Fetch a single page of raindrops from the API."""
        params = {
            "page": page, 
            "perpage": perpage,
            "sort": "-created"
        }
        
        if since_timestamp:
            try:
                since_dt = datetime.fromisoformat(since_timestamp.replace("Z", "+00:00"))
                since_unix = int(since_dt.timestamp())
                params["lastUpdate"] = since_unix
            except Exception as e:
                print(f"\\nWarning: Invalid timestamp format {since_timestamp}: {e}")
                print("Proceeding without timestamp filter...")

        response = requests.get(
            f"{self.base_url}/raindrops/0",
            headers=self.headers,
            params=params,
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch raindrops: {response.status_code} - {response.text}")

        return response.json().get("items", [])

    def fetch_raindrops(self, max_items=None, since_timestamp=None):
        """Fetch raindrops from API with optional timestamp filtering.
        Returns list of raindrops, optionally limited by count or timestamp.
        """
        all_raindrops = []
        page = 0

        if since_timestamp:
            print(f"Fetching raindrops since {since_timestamp}...")
        else:
            print("Fetching raindrops from all collections...")

        while True:
            if max_items:
                remaining = max_items - len(all_raindrops)
                if remaining <= 0:
                    break
                perpage = min(DEFAULT_PAGE_SIZE, remaining)
            else:
                perpage = DEFAULT_PAGE_SIZE

            print(f"  Fetching page {page + 1}...", end=" ")

            try:
                raindrops = self._fetch_page(page, perpage, since_timestamp)
            except Exception as e:
                print(f"\\n{e}")
                break

            if not raindrops:
                print("(no more items)")
                break

            # If using timestamp filter, check if we've gone too far back
            if since_timestamp and raindrops:
                oldest_in_page = min(raindrops, key=lambda x: x["created"])["created"]
                if oldest_in_page < since_timestamp:
                    filtered_raindrops = [r for r in raindrops if r["created"] >= since_timestamp]
                    print(f"got {len(filtered_raindrops)} new items (filtered from {len(raindrops)})")
                    all_raindrops.extend(filtered_raindrops)
                    break
                    
            print(f"got {len(raindrops)} items")
            all_raindrops.extend(raindrops)
            page += 1

            if max_items and len(all_raindrops) >= max_items:
                break

        print(f"Total raindrops fetched: {len(all_raindrops)}")
        return all_raindrops

    def reset_data(self):
        """Delete all raindrops and cache to start fresh"""
        if self.drops_dir.exists():
            print(f"Removing existing raindrops directory: {self.drops_dir}")
            shutil.rmtree(self.drops_dir)

        if self.cache_file.exists():
            print(f"Removing cache file: {self.cache_file}")
            self.cache_file.unlink()

        print("Reset complete - all data cleared")

    def _determine_sync_mode(self, reset, count, cache):
        """Determine sync mode and return new raindrops to process."""
        if reset:
            print("Reset mode: Rebuilding raindrops from scratch...")
            raindrops = self.fetch_raindrops(max_items=count)
            return raindrops, set()
        
        last_sync = cache.get("last_sync_timestamp")
        downloaded_ids = set(cache.get("downloaded", []))
        
        if last_sync:
            print(f"Incremental sync mode: fetching raindrops since {last_sync}")
            raindrops = self.fetch_raindrops(max_items=count, since_timestamp=last_sync)
            # Add deduplication even for incremental sync
            new_drops = [r for r in raindrops if str(r["_id"]) not in downloaded_ids]
            return new_drops, downloaded_ids
        else:
            print("First sync: fetching recent raindrops...")
            fetch_limit = count * FETCH_MULTIPLIER if count else DEFAULT_FIRST_SYNC_LIMIT
            raindrops = self.fetch_raindrops(max_items=fetch_limit)
            new_drops = [r for r in raindrops if str(r["_id"]) not in downloaded_ids]
            
            if count is not None and count > 0:
                new_drops = new_drops[:count]
                
            return new_drops, downloaded_ids

    def _write_raindrops_to_files(self, new_drops):
        """Write raindrops to markdown files and return created filenames."""
        created_filenames = []
        counter = 1
        
        # Get existing filenames to avoid overwrites
        existing_files = set()
        if self.drops_dir.exists():
            existing_files = {f.name for f in self.drops_dir.glob("*.md")}
        
        for i, raindrop in enumerate(new_drops, 1):
            filename = generate_raindrop_filename(raindrop, counter)
            filepath = self.drops_dir / filename
            
            # Skip if file already exists (additional duplicate protection)
            if filename in existing_files:
                print(f"  [{i}/{len(new_drops)}] Skipping existing: {filename}")
                counter += 1
                continue

            print(
                f"  [{i}/{len(new_drops)}] Writing: {filename} - {raindrop.get('title', 'Untitled')[:50]}..."
            )

            markdown_content = format_raindrop_as_markdown(raindrop)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            created_filenames.append(filename)
            counter += 1
            
        return created_filenames

    def _update_cache(self, cache, new_drops, downloaded_ids, reset):
        """Update cache with new timestamp and downloaded IDs."""
        cache["downloaded"] = downloaded_ids
        
        if new_drops:
            newest_timestamp = max(drop["created"] for drop in new_drops)
            cache["last_sync_timestamp"] = newest_timestamp
            print(f"Updated last sync timestamp to: {newest_timestamp}")
        elif reset or not cache.get("last_sync_timestamp"):
            cache["last_sync_timestamp"] = datetime.now().isoformat() + "Z"
            print(f"Set initial timestamp to: {cache['last_sync_timestamp']}")
            
        self.save_cache(cache)

    def download_raindrops(self, reset=False, count=None, rebuild_cache=False):
        """Download raindrops from API and save as markdown files."""
        try:
            self.authenticate()

            if reset:
                self.reset_data()
            elif rebuild_cache:
                self.rebuild_cache_from_files()

            self.drops_dir.mkdir(exist_ok=True)
            cache = self.load_cache()

            new_drops, downloaded_ids = self._determine_sync_mode(reset, count, cache)
            
            if not new_drops:
                print("No new raindrops to download")
                return []
                
            print(f"Found {len(new_drops)} new raindrops")
            
            created_filenames = self._write_raindrops_to_files(new_drops)
            
            # Update downloaded_ids with new drops
            for raindrop in new_drops:
                downloaded_ids.add(str(raindrop["_id"]))
                
            self._update_cache(cache, new_drops, downloaded_ids, reset)

            print(f"Downloaded {len(new_drops)} raindrops to {self.drops_dir}")
            
            if cache.get("last_sync_timestamp"):
                print(f"Next sync will only fetch raindrops newer than {cache['last_sync_timestamp']}")
                
            return created_filenames
        except Exception as e:
            print(f"Error downloading raindrops: {e}")
            return []