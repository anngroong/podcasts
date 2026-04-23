#!/usr/bin/env python3

# Extract youtube links from episodes

from pathlib import Path
import tomllib
import re

EPISODE_DIR = Path("content/episode")

def extract_front_matter(text: str):
    m = re.match(r"^\+\+\+\s*\n(.*?)\n\+\+\+\s*", text, re.DOTALL)
    return m.group(1) if m else None

results = []

for md_file in EPISODE_DIR.rglob("*.md"):
    try:
        text = md_file.read_text(encoding="utf-8")
        fm = extract_front_matter(text)
        if not fm:
            continue

        data = tomllib.loads(fm)

        episode = data.get("episode")
        youtube_id = data.get("youtube")

        if episode and youtube_id:
            results.append((int(episode), youtube_id))

    except Exception:
        continue

# sort numerically by episode
results.sort(key=lambda x: x[0])

# print output
for ep, yt in results:
    print(f"{ep} https://youtu.be/{yt}")
