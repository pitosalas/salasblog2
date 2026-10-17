#!/usr/bin/env python3
# wayback — Recover title and date of archived legacy salas.com posts from the Wayback Machine
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-17
# Updated: 2026-10-17
"""
Movable Type URLs (`/weblogs/archives/000522.html`) carry only an opaque
numeric ID, and nothing in current post frontmatter records it. The Wayback
Machine still has those pages, so their title and date are recovered from
the earliest 200 snapshot and used to match the current post.

Lookups use one CDX index query per directory, then the raw page (`id_` form, no Wayback
toolbar). Results - including "no snapshot" - are cached in one JSON file
keyed by normalized legacy path, so reruns never hit archive.org again for
a path already looked up. Live requests are spaced by `REQUEST_INTERVAL_S`.
"""

import html
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import requests

CDX_URL = "http://web.archive.org/cdx/search/cdx"
SNAPSHOT_URL = "http://web.archive.org/web/{timestamp}id_/{original}"
REQUEST_INTERVAL_S = 3
REQUEST_TIMEOUT_S = 60
# archive.org throttles with 429/503; back off and retry a bounded number of times.
THROTTLE_STATUSES = {429, 503}
THROTTLE_RETRY_WAITS_S = (10, 30, 60, 120)

TITLE_TAG = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DC_DATE = re.compile(r'dc:date="(\d{4}-\d{2}-\d{2})')
DATE_HEADER = re.compile(r'<h2 class="date">\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})\s*</h2>')
POSTED_ON = re.compile(r"Posted by [^<]*? on ([A-Za-z]+\s+\d{1,2},\s+\d{4})")
BLOG_TITLE_PREFIX = "Pito's Blog: "


@dataclass(frozen=True)
class ArchivedPost:
    title: str
    date: str
    snapshot_url: str


def parse_archived_post(page_html: str, snapshot_url: str) -> ArchivedPost:
    """Title and ISO date of an archived Movable Type entry page."""
    title_match = TITLE_TAG.search(page_html)
    if title_match is None:
        raise ValueError(f"No <title> in archived page {snapshot_url}")
    title = html.unescape(" ".join(title_match.group(1).split()))
    title = title.removeprefix(BLOG_TITLE_PREFIX)
    return ArchivedPost(
        title, parse_archived_date(page_html, snapshot_url), snapshot_url
    )


def parse_archived_date(page_html: str, snapshot_url: str) -> str:
    dc_match = DC_DATE.search(page_html)
    if dc_match is not None:
        return dc_match.group(1)
    for pattern in (DATE_HEADER, POSTED_ON):
        match = pattern.search(page_html)
        if match is not None:
            date_text = " ".join(match.group(1).split())
            return datetime.strptime(date_text, "%B %d, %Y").date().isoformat()
    raise ValueError(f"No entry date in archived page {snapshot_url}")


def get_with_retry(session: requests.Session, url: str, **kwargs) -> requests.Response:
    for wait_s in (*THROTTLE_RETRY_WAITS_S, None):
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT_S, **kwargs)
        except requests.Timeout:
            if wait_s is None:
                raise
        else:
            if response.status_code not in THROTTLE_STATUSES or wait_s is None:
                break
        time.sleep(wait_s)
    response.raise_for_status()
    return response


def snapshot_index(directory: str, session: requests.Session) -> dict[str, str]:
    """
    Earliest 200 snapshot URL for every archived page under
    salas.com<directory>, keyed by path. One CDX request covers the whole
    directory; `collapse=urlkey` keeps the first (earliest) capture per URL.
    """
    response = get_with_retry(
        session,
        CDX_URL,
        params={
            "url": f"salas.com{directory}",
            "matchType": "prefix",
            "output": "json",
            "fl": "timestamp,original",
            "filter": "statuscode:200",
            "collapse": "urlkey",
        },
    )
    rows = response.json() if response.text.strip() else []
    index = {}
    for timestamp, original in rows[1:]:
        path = urlsplit(original).path
        index.setdefault(
            path, SNAPSHOT_URL.format(timestamp=timestamp, original=original)
        )
    return index


def fetch_archived_post(snapshot_url: str, session: requests.Session) -> ArchivedPost:
    response = get_with_retry(session, snapshot_url)
    return parse_archived_post(response.text, snapshot_url)


def resolve_paths(paths: list[str], cache_file: Path) -> dict[str, ArchivedPost | None]:
    """
    Archived post for each legacy path (None when archive.org has no 200
    snapshot). Cached entries are reused; new ones are written back to
    cache_file after each lookup so an interrupted run loses nothing.
    """
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}
    uncached = [path for path in paths if path not in cache]
    session = requests.Session()
    index = {}
    for directory in sorted({path.rsplit("/", 1)[0] + "/" for path in uncached}):
        index.update(snapshot_index(directory, session))
    for path in uncached:
        snapshot_url = index.get(path)
        archived = (
            None if snapshot_url is None else fetch_archived_post(snapshot_url, session)
        )
        cache[path] = None if archived is None else asdict(archived)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cache, indent=2, sort_keys=True))
        time.sleep(REQUEST_INTERVAL_S)
    return {
        path: None if cache[path] is None else ArchivedPost(**cache[path])
        for path in paths
    }
