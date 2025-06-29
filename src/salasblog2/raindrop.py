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
        self.cache_file = Path("content/.rd_cache.json")

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
        # Try to load from environment variable first (persists across restarts)
        env_timestamp = os.getenv("RAINDROP_LAST_SYNC")
        if env_timestamp:
            print(f"Using cached timestamp from environment: {env_timestamp}")
            return {"last_sync_timestamp": env_timestamp, "downloaded": set()}
            
        if self.cache_file.exists():
            with open(self.cache_file, "r") as f:
                cache = json.load(f)
                # Convert old ID-based cache to new timestamp-based cache
                if "downloaded" in cache and "last_sync_timestamp" not in cache:
                    print("Converting old cache format to timestamp-based...")
                    cache = {"last_sync_timestamp": None, "downloaded": set(cache["downloaded"])}
                return cache
        return {"last_sync_timestamp": None, "downloaded": set()}

    def save_cache(self, cache):
        # Create a copy for serialization
        cache_copy = cache.copy()
        cache_copy["downloaded"] = list(cache_copy["downloaded"])
        with open(self.cache_file, "w") as f:
            json.dump(cache_copy, f, indent=2)
        
        # Also save timestamp to environment for backup
        if cache.get("last_sync_timestamp"):
            print(f"Cache saved - next sync will fetch raindrops newer than {cache['last_sync_timestamp']}")

    def fetch_raindrops(self, max_items=None, since_timestamp=None):
        """
        Fetch raindrops from Raindrop.io API with optional timestamp filtering.
        
        Args:
            max_items: Maximum number of items to fetch (None for all)
            since_timestamp: ISO timestamp to fetch only newer raindrops (None for all)
        """
        all_raindrops = []
        page = 0

        if since_timestamp:
            print(f"Fetching raindrops since {since_timestamp}...")
        else:
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

            # Build API parameters
            params = {
                "page": page, 
                "perpage": perpage,
                "sort": "-created"  # Sort by creation date, newest first
            }
            
            # Add timestamp filter if provided
            if since_timestamp:
                # Convert ISO timestamp to Unix timestamp for API
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
                print(f"\\nFailed to fetch raindrops: {response.status_code}")
                print(f"Response: {response.text}")
                break

            data = response.json()
            raindrops = data.get("items", [])

            if not raindrops:
                print("(no more items)")
                break

            # If using timestamp filter, check if we've gone too far back
            if since_timestamp and raindrops:
                oldest_in_page = min(raindrops, key=lambda x: x["created"])["created"]
                if oldest_in_page < since_timestamp:
                    # Filter out items older than our timestamp
                    filtered_raindrops = [r for r in raindrops if r["created"] >= since_timestamp]
                    print(f"got {len(filtered_raindrops)} new items (filtered from {len(raindrops)})")
                    all_raindrops.extend(filtered_raindrops)
                    break  # No need to fetch more pages
                    
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
            print("Reset mode: Rebuilding raindrops from scratch...")
            raindrops = self.fetch_raindrops(max_items=count)
            new_drops = raindrops
            downloaded_ids = set()  # Start with empty cache
            print(f"Rebuilding {len(new_drops)} raindrops")
        else:
            # Incremental mode - use timestamp-based filtering
            last_sync = cache.get("last_sync_timestamp")
            
            if last_sync:
                print(f"Incremental sync mode: fetching raindrops since {last_sync}")
                # Fetch only new raindrops since last sync
                raindrops = self.fetch_raindrops(max_items=count, since_timestamp=last_sync)
                
                # No need to check downloaded_ids since we're using timestamp filtering
                new_drops = raindrops
                downloaded_ids = set(cache.get("downloaded", []))
                
                if not new_drops:
                    print("No new raindrops since last sync")
                    return []
                    
                print(f"Found {len(new_drops)} new raindrops since last sync")
            else:
                print("First sync: fetching recent raindrops...")
                # First time sync - fetch recent items and use ID-based deduplication as fallback
                fetch_limit = count * 2 if count else 100  # Reasonable default for first sync
                raindrops = self.fetch_raindrops(max_items=fetch_limit)
                
                downloaded_ids = set(cache.get("downloaded", []))
                new_drops = [r for r in raindrops if str(r["_id"]) not in downloaded_ids]
                
                if not new_drops:
                    print("No new raindrops to download")
                    return []
                    
                print(f"Found {len(new_drops)} new raindrops")
                
                # Limit the number of drops if count is specified
                if count is not None and count > 0:
                    new_drops = new_drops[:count]
                    print(f"Limiting to first {len(new_drops)} raindrops")

        # Track the newest timestamp for next incremental sync
        newest_timestamp = None
        if new_drops:
            newest_timestamp = max(drop["created"] for drop in new_drops)

        # Track created filenames for incremental regeneration
        created_filenames = []
        counter = 1
        for i, raindrop in enumerate(new_drops, 1):
            filename = generate_raindrop_filename(raindrop, counter)
            filepath = self.drops_dir / filename

            print(
                f"  [{i}/{len(new_drops)}] Writing: {filename} - {raindrop.get('title', 'Untitled')[:50]}..."
            )

            markdown_content = format_raindrop_as_markdown(raindrop)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            downloaded_ids.add(str(raindrop["_id"]))
            created_filenames.append(filename)
            counter += 1

        # Update cache with new timestamp and IDs
        cache["downloaded"] = downloaded_ids
        if newest_timestamp:
            cache["last_sync_timestamp"] = newest_timestamp
            print(f"Updated last sync timestamp to: {newest_timestamp}")
        elif reset or not cache.get("last_sync_timestamp"):
            # For first sync or reset, set timestamp to now to prevent re-downloading
            from datetime import datetime
            cache["last_sync_timestamp"] = datetime.now().isoformat() + "Z"
            print(f"Set initial timestamp to: {cache['last_sync_timestamp']}")
            
        self.save_cache(cache)

        print(f"Downloaded {len(new_drops)} raindrops to {self.drops_dir}")
        
        # Performance info
        if cache.get("last_sync_timestamp"):
            print(f"Next sync will only fetch raindrops newer than {cache['last_sync_timestamp']}")
            
        # Return list of created filenames for incremental regeneration
        return created_filenames