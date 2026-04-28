#!/usr/bin/env python3

import argparse
import re
from pathlib import Path


def decode_html(raw: bytes):
    """
    Decode HTML while preserving legacy encodings.
    Returns: (decoded_text, encoding_used)
    """

    encodings = []

    # Detect charset from meta tag, if present
    m = re.search(br'charset=["\']?([A-Za-z0-9_\-]+)', raw, re.I)
    if m:
        encodings.append(m.group(1).decode("ascii", errors="ignore"))

    # Common fallbacks for older static archives
    encodings += [
        "utf-8",
        "windows-1252",
        "iso-8859-1",
        "utf-16",
    ]

    tried = []

    for enc in encodings:
        if not enc or enc.lower() in tried:
            continue

        tried.append(enc.lower())

        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(
        "html",
        raw,
        0,
        1,
        f"Could not decode with: {tried}",
    )


def build_canonical_url(path: Path, site_root: Path, base_url: str) -> str:
    rel_path = path.relative_to(site_root)

    if rel_path.name == "index.html":
        parent = rel_path.parent.as_posix()
        url_path = "/" if parent == "." else f"/{parent}/"
    else:
        url_path = "/" + rel_path.as_posix()

    return base_url.rstrip("/") + url_path


def has_canonical(content: str) -> bool:
    return re.search(
        r'<link\b[^>]*rel=["\']canonical["\']',
        content,
        re.I,
    ) is not None


def insert_canonical(content: str, canonical_url: str):
    canonical_tag = (
        f'    <link rel="canonical" href="{canonical_url}" />\n'
    )

    new_content, count = re.subn(
        r'(<head\b[^>]*>)',
        r'\1\n' + canonical_tag,
        content,
        count=1,
        flags=re.I,
    )

    return new_content, count > 0


def main():
    parser = argparse.ArgumentParser(
        description="Add canonical links to static HTML files."
    )

    parser.add_argument(
        "site_root",
        help="Path to the static site root",
    )

    parser.add_argument(
        "--base-url",
        required=True,
        help="Base URL, e.g. https://groong.org",
    )

    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files",
    )

    args = parser.parse_args()

    site_root = Path(args.site_root).expanduser().resolve()
    base_url = args.base_url.rstrip("/")

    files_found = 0
    files_changed = 0
    files_failed = 0
    files_skipped_existing = 0
    files_skipped_no_head = 0

    print(f"Site root: {site_root}")
    print(f"Exists:    {site_root.exists()}")
    print(f"Is dir:    {site_root.is_dir()}")
    print(f"Base URL:  {base_url}")
    print(f"Dry run:   {args.dry_run}")
    print()

    if not site_root.exists() or not site_root.is_dir():
        print("ERROR: site_root does not exist or is not a directory")
        return 1

    for path in site_root.rglob("*.html"):
        files_found += 1

        try:
            raw = path.read_bytes()
            content, encoding = decode_html(raw)
        except Exception as e:
            files_failed += 1
            print(f"READ ERROR: {path}: {e}")
            continue

        if has_canonical(content):
            files_skipped_existing += 1
            continue

        canonical_url = build_canonical_url(path, site_root, base_url)
        new_content, inserted = insert_canonical(content, canonical_url)

        if not inserted:
            files_skipped_no_head += 1
            print(f"SKIP no <head>: {path}")
            continue

        if new_content == content:
            continue

        files_changed += 1

        if args.dry_run:
            print(f"WOULD UPDATE [{encoding}]: {path}")
            print(f"  canonical: {canonical_url}")
        else:
            try:
                path.write_bytes(new_content.encode(encoding))
                print(f"UPDATED [{encoding}]: {path}")
                print(f"  canonical: {canonical_url}")
            except Exception as e:
                files_failed += 1
                files_changed -= 1
                print(f"WRITE ERROR: {path}: {e}")

    print()
    print("Summary")
    print("-------")
    print(f"HTML files found:           {files_found}")
    print(f"Files changed:              {files_changed}")
    print(f"Skipped existing canonical: {files_skipped_existing}")
    print(f"Skipped missing <head>:     {files_skipped_no_head}")
    print(f"Failed files:               {files_failed}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
