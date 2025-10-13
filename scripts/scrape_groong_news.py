#!/usr/bin/env python3
"""
Groong news scraper — JSON only

- Outputs all_news.json
- Supports --date YYYYMMDD and crawls only that day's section in the index
- Robust day extraction: collect links from a day's <strong> marker up to the next day's marker
"""

import re
import json
import argparse
import hashlib
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
from datetime import datetime, timezone
from dateutil import parser as dateparser

# ---------------- Config ----------------
BASE_URL = "https://groong.org/news/index.html"
DOMAIN   = "https://groong.org"
MAX_ARTICLES = 1000

# -------------- Regex helpers -----------
MSG_ID_RE     = re.compile(r"msg(\d+)\.html", re.I)
URL_RE        = re.compile(r"https?://\S+")
DATE_LINE_RE  = re.compile(r"^\s*Date:\s*(.+)$", re.MULTILINE)
ARMENIAN_RE   = re.compile(r'[\u0530-\u058F]')  # simple heuristic

# -------------- Utilities ---------------
def canonicalize(url: str) -> str:
    if not url:
        return url
    u = url.strip()
    if u.startswith("//"):
        u = "https:" + u
    if u.startswith("/"):
        u = urljoin(DOMAIN, u)
    parts = urlparse(u)
    scheme = "https"
    netloc = parts.netloc or "groong.org"
    path = parts.path
    return f"{scheme}://{netloc}{path}"

def extract_msg_id(groong_link: str):
    m = MSG_ID_RE.search(groong_link or "")
    return int(m.group(1)) if m else None

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def guess_lang(text: str) -> str:
    return "hy" if ARMENIAN_RE.search(text or "") else "und"

def parse_posted_date_from_page(soup: BeautifulSoup):
    full_text = soup.get_text("\n", strip=True)
    m = DATE_LINE_RE.search(full_text)
    if not m:
        return None, None
    raw = m.group(1).strip()
    iso = None
    try:
        dt = dateparser.parse(raw)
        if dt.tzinfo:
            iso = dt.isoformat()
        else:
            iso = dt.replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        iso = None
    return raw, iso

def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\u00A0", " ")).strip()

def yyyymmdd_to_parts(yyyymmdd: str):
    dt = datetime.strptime(yyyymmdd, "%Y%m%d")
    month_name = ["January","February","March","April","May","June","July",
                  "August","September","October","November","December"][dt.month-1]
    # Weekday is not needed anymore; we only match the date triple.
    return dt.year, month_name, dt.day

def build_day_date_regex(yyyymmdd: str) -> re.Pattern:
    """
    Match just '11 October 2025' (ignore weekday/prefix & allow flexible spaces)
    Example header: 'News Articles on -- Saturday,  11 October 2025'
    """
    year, month_name, day = yyyymmdd_to_parts(yyyymmdd)
    return re.compile(rf"\b{day}\s+{re.escape(month_name)}\s+{year}\b", re.I)

# ----------- Scrape index ---------------
def get_article_links_all(index_url):
    r = requests.get(index_url, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        h = a["href"].strip()
        if MSG_ID_RE.fullmatch(h):
            links.append(f"{DOMAIN}/news/{h}")

    seen, dedup = set(), []
    for u in links:
        if u not in seen:
            dedup.append(u); seen.add(u)
    return dedup

def collect_links_between_day_markers(soup: BeautifulSoup, date_re: re.Pattern):
    """
    Find the <strong> that contains the target date (e.g., '11 October 2025'),
    then iterate forward through .next_elements until the next <strong> that
    starts with 'News Articles on --', collecting msgNNNNNN.html hrefs.
    This is robust against the malformed list structure in the index.
    """
    # locate the start <strong>
    start = None
    for st in soup.find_all("strong"):
        if date_re.search(normalize_spaces(st.get_text(" ", strip=True))):
            start = st
            break
    if not start:
        return None, []  # signal "not found"

    links = []
    for el in start.next_elements:
        if isinstance(el, Tag) and el.name == "strong":
            # day header markers look like 'News Articles on -- ...'
            t = normalize_spaces(el.get_text(" ", strip=True))
            if el is not start and t.startswith("News Articles on --"):
                break
        if isinstance(el, Tag) and el.name == "a" and el.has_attr("href"):
            h = el["href"].strip()
            if MSG_ID_RE.fullmatch(h):
                links.append(f"{DOMAIN}/news/{h}")

    # de-dup while preserving order
    seen, out = set(), []
    for u in links:
        if u not in seen:
            out.append(u); seen.add(u)
    return start, out

def get_article_links_for_day(index_url, yyyymmdd):
    r = requests.get(index_url, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    date_re = build_day_date_regex(yyyymmdd)
    start, links = collect_links_between_day_markers(soup, date_re)
    if start is None:
        print(f"[warn] Could not locate day header for {yyyymmdd}; falling back to full scan.")
        return get_article_links_all(index_url)

    if not links:
        print(f"[warn] Day header found for {yyyymmdd} but no message links collected; falling back to full scan.")
        return get_article_links_all(index_url)

    print(f"[info] Found {len(links)} links under the {yyyymmdd} day block.")
    return links

# ----------- Scrape article -------------
def scrape_article(url):
    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Untitled Article"

    body_div = soup.find("div", attrs={"dir": "ltr"})
    content  = body_div.get_text(separator="\n", strip=True) if body_div else ""

    source_urls = sorted({canonicalize(u) for u in URL_RE.findall(content)})

    groong_link = canonicalize(url)
    aid = extract_msg_id(groong_link)

    posted_date_raw, posted_date_iso = parse_posted_date_from_page(soup)
    lang = guess_lang(content)

    return {
        "id": aid,
        "groong_link": groong_link,
        "title": title,
        "content": content,
        "source_urls": source_urls,
        "lang": lang,
        "sha256": sha256_text((title or "") + "\n" + (content or "")),
        "posted_date_raw": posted_date_raw,
        "posted_date_iso": posted_date_iso,
    }

# --------------- Writer -----------------
def save_all_news_json(records, path="all_news.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"wrote {path} ({len(records)} items)")

# ---------------- Main ------------------
def scrape_all_news(target_date=None):
    if target_date:
        urls = get_article_links_for_day(BASE_URL, target_date)
    else:
        urls = get_article_links_all(BASE_URL)

    total = min(MAX_ARTICLES, len(urls))
    records = []
    for i, url in enumerate(urls[:total]):
        print(f"Scraping ({i+1}/{total}): {url}")
        rec = scrape_article(url)
        if not rec:
            continue

        # Safety: verify page date when filtering
        if target_date and rec.get("posted_date_iso"):
            try:
                dt = datetime.fromisoformat(rec["posted_date_iso"].replace("Z", "+00:00"))
                if dt.astimezone(timezone.utc).strftime("%Y%m%d") != target_date:
                    continue
            except Exception:
                continue

        records.append(rec)

    records.sort(key=lambda x: (x["id"] is None, x["id"]))

    if not records:
        print("No news articles matched the criteria.")
        return

    save_all_news_json(records, "all_news.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Groong news archive (JSON only)")
    parser.add_argument(
        "--date",
        help="Scrape only articles posted on this UTC date (YYYYMMDD); collects links between day markers in the index",
        required=False,
    )
    args = parser.parse_args()
    scrape_all_news(target_date=args.date)

