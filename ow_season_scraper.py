#!/usr/bin/env python3
"""
Overwatch Patch Notes Scraper (simplified)
===========================================

Scrapes https://overwatch.blizzard.com/en-us/news/patch-notes/ to figure
out the current in-game season, and dumps {season, season_title,
latest_patch_date} to a JSON file.

Note on "season numbering": in Feb 2026 Blizzard rebranded the game back to
"Overwatch" and reset season numbering to 1 under the year-long "Reign of
Talon" storyline. So "Season 3" today means "Reign of Talon - Season 3".

CAVEAT: the patch-notes page is client-side-rendered. A plain HTTP GET only
returns the newest post -- if that post doesn't happen to mention "Season
N" (e.g. an anti-cheat announcement), there's nothing on the page to match.
To handle that, this script caches the last successfully-scraped season and
carries it forward (marked "stale": true) when a fresh scrape comes up
empty, since a season number that was true a few days ago is almost
certainly still true today. There is no fan-site fallback -- if the
official site is unreachable, we fall straight back to the cache.

Usage:
    python ow_season_scraper.py                 # scrape + write ow_season_cache.json
    python ow_season_scraper.py -o custom.json   # write to a custom path
    python ow_season_scraper.py -v               # verbose logging to stderr
    python ow_season_scraper.py --no-cache       # ignore/don't consult the cache

Importable usage:
    from ow_season_scraper import gather_data
    season, title, patch_date = gather_data()
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
DEFAULT_OUTPUT = STORAGE_DIR / "ow_season_cache.json"

OFFICIAL_URL = "https://overwatch.blizzard.com/en-us/news/patch-notes/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Ordered most-specific -> least-specific. Stop at the first match.
SEASON_PATTERNS = [
    re.compile(r"Reign of Talon\s*[:\-\u2013]*\s*Season\s+(\d+)", re.I),
    re.compile(r"Season\s+(\d+)\s*[:\-\u2013]\s*[A-Z][\w' ]+", re.I),
    re.compile(r"\bSeason\s+(\d+)\b", re.I),
]

# Grabs just the title, e.g. "Reign of Talon - Season 4: Heroes of Busan"
# -> "Heroes of Busan". The separator before/after "Season N" flips between
# "-" and ":" from one season to the next (compare "Reign of Talon -
# Season 4: Heroes of Busan" to "Reign of Talon: Season 3 - Into The
# Tiger's Den"), so this just takes everything after "Season N<sep>" to
# the end of whatever line it's given. It's meant to be run on an isolated
# "Reign of Talon ... Season N ... Title" line (see find_season_line())
# rather than the whole flattened page text -- on the real page the title
# is followed immediately by body copy with no punctuation in between
# (they're separate HTML elements), so trimming at end-of-line only works
# once that line has already been isolated from the rest of the page.
SEASON_TITLE_PATTERN = re.compile(r"Season\s+\d+\s*[:\-\u2013]\s*(.+)$")

# Fallback anchor used only when we can't isolate a clean title line from
# the DOM (see find_season_line()) and have to search the flattened page
# text instead. Less reliable -- trims at the next sentence-ending
# punctuation/comma, which is a guess, not a real boundary.
SEASON_TITLE_PATTERN_FLAT_FALLBACK = re.compile(
    r"Reign of Talon\s*[:\-\u2013]\s*Season\s+\d+\s*[:\-\u2013]\s*([^.!?\n,]+)"
)

DATE_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},\s+\d{4}"
)


def log(verbose: bool, *nargs) -> None:
    if verbose:
        print("[ow_season_scraper]", *nargs, file=sys.stderr)


def find_season_line(soup: BeautifulSoup) -> Optional[str]:
    """Find the specific HTML element that holds just the season heading,
    e.g. "Reign of Talon - Season 4: Heroes of Busan", isolated from the
    body copy that follows it.

    The patch-notes page puts this in its own heading/paragraph tag, so we
    scan all tags for ones whose own text matches "Reign of Talon ...
    Season N" and are short enough to plausibly be just that heading (not
    some large wrapping <div> that happens to contain the heading plus
    everything after it). Among matches, the shortest is the most
    specific/innermost one.
    """
    pattern = re.compile(r"Reign of Talon.*Season\s+\d+", re.I)
    candidates = []
    for tag in soup.find_all(True):
        text = tag.get_text(" ", strip=True)
        if text and len(text) < 150 and pattern.search(text):
            candidates.append(text)
    return min(candidates, key=len) if candidates else None


def extract_season_info(text: str, season_line: Optional[str] = None) -> dict:
    """Given plain page text (and, ideally, an isolated season/title line
    from find_season_line()), pull out the current season number/title/date.
    """
    season_source = season_line or text

    season_number: Optional[int] = None
    for pattern in SEASON_PATTERNS:
        match = pattern.search(season_source)
        if match:
            season_number = int(match.group(1))
            break

    if season_line:
        title_match = SEASON_TITLE_PATTERN.search(season_line)
    else:
        title_match = SEASON_TITLE_PATTERN_FLAT_FALLBACK.search(text)
    season_title = title_match.group(1).strip().rstrip(",.") if title_match else None

    date_match = DATE_PATTERN.search(text)
    latest_patch_date = date_match.group(0) if date_match else None

    return {
        "season": season_number,
        "season_title": season_title,
        "latest_patch_date": latest_patch_date,
    }


def scrape_official(verbose: bool = False) -> dict:
    log(verbose, f"GET {OFFICIAL_URL}")
    resp = requests.get(OFFICIAL_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    season_line = find_season_line(soup)
    log(verbose, f"Isolated season line: {season_line!r}")
    info = extract_season_info(text, season_line=season_line)
    info["scraped_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return info


def load_cache(path: str, verbose: bool = False) -> Optional[dict]:
    """Load a previous run's output, if present and parseable."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            cached = json.load(f)
        if cached.get("season") is not None:
            return cached
    except (OSError, json.JSONDecodeError) as exc:
        log(verbose, f"Could not read cache at {path}: {exc}")
    return None


def apply_cache_fallback(result: dict, cache: Optional[dict], verbose: bool = False) -> dict:
    """If today's scrape didn't find a season (or the site was unreachable),
    carry the last known-good season forward instead of reporting total
    failure. A season that was live a few days ago is almost certainly
    still live today -- these things run for weeks, not hours.
    """
    if result.get("season") is not None:
        result["stale"] = False
        return result

    if cache is None:
        result["stale"] = False  # nothing to fall back to; genuinely unknown
        return result

    log(verbose, f"No season found today; carrying forward cached season {cache.get('season')}")
    result["season"] = cache.get("season")
    result["season_title"] = cache.get("season_title")
    result["latest_patch_date"] = result.get("latest_patch_date") or cache.get("latest_patch_date")
    result["stale"] = True
    result["stale_since"] = cache.get("scraped_at_utc")
    return result


def gather_data(
    output: str = DEFAULT_OUTPUT,
    use_cache: bool = True,
    verbose: bool = False,
):
    """Scrape (with cache fallback), write `output`, and return
    (season, season_title, latest_patch_date).
    """
    cache = load_cache(output, verbose=verbose) if use_cache else None

    try:
        data = scrape_official(verbose=verbose)
    except Exception as exc:  # noqa: BLE001 - any failure -> rely on cache fallback
        log(verbose, f"Official site failed: {exc}")
        data = {
            "season": None,
            "season_title": None,
            "latest_patch_date": None,
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "error": str(exc),
        }

    data = apply_cache_fallback(data, cache, verbose=verbose)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return data.get("season"), data.get("season_title"), data.get("latest_patch_date")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape the current Overwatch season.")
    parser.add_argument(
        "-o", "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to write the JSON result to"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print progress to stderr")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't fall back to the last known-good season if today's scrape finds nothing",
    )
    args = parser.parse_args()

    season, title, patch_date = gather_data(
        output=args.output, use_cache=not args.no_cache, verbose=args.verbose
    )

    if season is not None:
        print(json.dumps({"season": season, "season_title": title, "latest_patch_date": patch_date}))
    else:
        sys.exit(1)