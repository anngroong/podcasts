#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrape daily news items from https://groong.org/news/
and save them as structured JSON optimized for summarization.

Key improvements:
- Extracts Groong (canonical) and external URLs separately.
- Cleans URLs out of the content body.
- Derives stable msg_id (e.g., 176700) from the Groong link.
- Adds short excerpt, slug, and lightweight keywords.
- Produces clean JSON for direct clustering/summarization.
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

BASE_URL = "https://groong.org/news/"
OUTFILE = Path("all_news.json")

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def clean_content_and_extract_urls(text):
    """Remove URLs from text and separate them cleanly."""
    if not text:
        return "", [], []
    all_urls = re.findall(r"https?://\S+", text)
    groong_urls = [u for u in all_urls if "groong.org" in u]
    external_urls = [u for u in all_urls if "groong.org" not in u]
    clean_text = text
    for u in all_urls:
        clean_text = clean_text.replace(u, "").strip()
    return clean_text.strip(), groong_urls, external_urls


def extract_msg_id(url):
    m = re.search(r"msg(\d+)\.html", url or "")
    return m.group(1) if m else None


STOPWORDS = set("""a an the of and or in to for from on with by at as is are was were will would should could have has had be being been that this those these it its they them their we you i our your his her him he she not""".split())

def simple_keywords(title):
    if not title:
        return []
    tokens = re.findall(r"[A-Za-z\u0530-\u058F]+", title.lower())  # includes Armenian letters
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2][:12]


def slugify(text):
    if not text:
        return None
    t = re.sub(r"[^0-9A-Za-z\u0530-\u058F]+", "-", text)
    t = re.sub(r"-{2,}", "-", t).strip("-").lower()
    return t[:120] if t else None


# ----------------------------------------------------------------------
# Main scraping logic
# ----------------------------------------------------------------------

def scrape_index():
    """Scrape the Groong news index and collect links to daily msg pages."""
    print(f"Fetching index: {BASE_URL}")
    resp = requests.get(BASE_URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = []
    for a in soup.select("a[href^='msg']"):
        href = a["href"]
        full_url = urljoin(BASE_URL, href)
        title = a.text.strip()
        links.append((title, full_url))
    print(f"Found {len(links)} entries on index page.")
    return links


def scrape_item(title, url):
    """Scrape individual msgNNNNNN.html page."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    paragraphs = soup.find_all("p")
    content = "\n".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
    clean_body, groong_urls, external_urls = clean_content_and_extract_urls(content)
    canonical_groong_url = groong_urls[0] if groong_urls else url
    msg_id = extract_msg_id(canonical_groong_url)

    item = {
        "id": msg_id or str(abs(hash(url)) % (10**8)),
        "title": title.strip(),
        "canonical_groong_url": canonical_groong_url,
        "external_urls": external_urls,
        "source_urls": [u for u in [canonical_groong_url] + external_urls if u],
        "content_excerpt": clean_body[:1000],
        "title_slug": slugify(title),
        "keywords": simple_keywords(title),
    }
    return item


def main():
    links = scrape_index()
    data = []
    for title, url in links:
        print(f"Scraping {url}")
        item = scrape_item(title, url)
        if item:
            data.append(item)

    print(f"Scraped {len(data)} total items.")
    with OUTFILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved cleaned data to {OUTFILE.resolve()}")


if __name__ == "__main__":
    main()

