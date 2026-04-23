#!/usr/bin/env python3
"""
Convert a Groong transcript plus Hugo episode file into a publishable Hugo
Markdown transcript post.

Repository-root workflow:
- Run from the podcasts repo root
- Provide only the show number, e.g. 532
- The script resolves:
    transcripts/532-*.txt
    content/episode/532-*.md

Example:
    python3 scripts/substack_to_hugo_transcript.py 532 -o content/post/532-transcript.md
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

try:
    import tomllib
except ModuleNotFoundError:
    print("This script requires Python 3.11+ (tomllib).", file=sys.stderr)
    raise

TRANSCRIPT_LINE_RE = re.compile(
    r"^(?P<speaker>[^\n(]+?)\s*\((?P<timestamp>\d{2}:\d{2}:\d{2})\):\s*(?P<text>.*)\s*$"
)
DESCRIPTION_LINK_RE = re.compile(r"\*\s*\[(?P<label>[^\]]+)\]\((?P<url>[^)]+)\)")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“‘(])")


@dataclass
class Segment:
    speaker: str
    timestamp: str
    text: str


@dataclass
class EpisodeMetadata:
    title: str
    subtitle: Optional[str]
    date: Optional[str]
    publish_date: Optional[str]
    youtube_id: Optional[str]
    episode: Optional[str]
    aliases: list[str]
    hosts: list[str]
    guests: list[str]
    categories: list[str]
    tags: list[str]
    description: Optional[str]
    summary: Optional[str]
    podcast_file: Optional[str]
    episode_image: Optional[str]
    episode_banner: Optional[str]
    images: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("show_number", help="Show number, e.g. 532")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output markdown path. If omitted, writes to content/blog/YYYYMMDD-transcript-<episode-filename>.md",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--site-base", default="https://podcasts.groong.org")
    parser.add_argument("--keep-timestamps", action="store_true")
    parser.add_argument("--title-prefix", default="Transcript: ")
    parser.add_argument("--description", default=None, help="Override front matter Description")
    parser.add_argument("--blog-image", default=None)
    parser.add_argument("--images-default", default=None)
    parser.add_argument("--author", default="")
    parser.add_argument("--alias", default="")
    parser.add_argument("--max-paragraph-chars", type=int, default=650)
    parser.add_argument("--max-paragraph-sentences", type=int, default=4)
    return parser.parse_args()


def find_single_prefixed_file(directory: Path, prefix: str, suffix: str) -> Path:
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    pattern = f"{prefix}-*{suffix}"
    matches = sorted(p for p in directory.glob(pattern) if p.is_file())

    if not matches:
        raise FileNotFoundError(f"No file found matching {directory / pattern}")

    if len(matches) > 1:
        names = "\n  - ".join(p.name for p in matches)
        raise FileExistsError(
            f"Multiple files found for prefix {prefix!r} in {directory}:\n  - {names}"
        )

    return matches[0]


def resolve_repo_files(repo_root: Path, show_number: str) -> tuple[Path, Path]:
    transcript_dir = repo_root / "transcripts"
    episode_dir = repo_root / "content" / "episode"
    transcript_path = find_single_prefixed_file(transcript_dir, show_number, ".txt")
    episode_path = find_single_prefixed_file(episode_dir, show_number, ".md")
    return transcript_path, episode_path


def split_front_matter(text: str) -> tuple[str, str]:
    if not text.startswith("+++\n"):
        raise ValueError("Episode file does not start with TOML front matter delimited by +++")
    parts = text.split("+++", 2)
    if len(parts) < 3:
        raise ValueError("Could not find closing +++ in episode file")
    _, front_matter, body = parts
    return front_matter.strip(), body.strip()


def _opt_str(value: object) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return []


def format_toml_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    s = value.strip()
    if "T" in s:
        return s.split("T", 1)[0]
    if " " in s:
        return s.split(" ", 1)[0]
    return s


def parse_episode_file(path: Path) -> EpisodeMetadata:
    raw = path.read_text(encoding="utf-8")
    front_matter_raw, body = split_front_matter(raw)
    data = tomllib.loads(front_matter_raw)

    summary = None
    if body.strip():
        cleaned = re.sub(r"^#\s+Summary\s*", "", body.strip(), flags=re.IGNORECASE).strip()
        summary = cleaned.split("\n\n", 1)[0].strip() if cleaned else None

    date = format_toml_date(_opt_str(data.get("Date")) or _opt_str(data.get("date")))
    publish_date = format_toml_date(
        _opt_str(data.get("PublishDate"))
        or _opt_str(data.get("publishDate"))
        or _opt_str(data.get("publishdate"))
        or date
    )

    return EpisodeMetadata(
        title=str(data.get("title", "")).strip(),
        subtitle=_opt_str(data.get("subtitle")),
        date=date,
        publish_date=publish_date,
        youtube_id=_opt_str(data.get("youtube")),
        episode=_opt_str(data.get("episode")),
        aliases=_string_list(data.get("aliases", [])),
        hosts=_string_list(data.get("hosts", [])),
        guests=_string_list(data.get("guests", [])),
        categories=_string_list(data.get("categories", [])),
        tags=_string_list(data.get("tags", [])),
        description=_opt_str(data.get("Description")) or _opt_str(data.get("description")),
        summary=summary,
        podcast_file=_opt_str(data.get("podcast_file")),
        episode_image=_opt_str(data.get("episode_image")),
        episode_banner=_opt_str(data.get("episode_banner")),
        images=_string_list(data.get("images", [])),
    )


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def parse_transcript(path: Path) -> list[Segment]:
    lines = path.read_text(encoding="utf-8").splitlines()
    segments: list[Segment] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        match = TRANSCRIPT_LINE_RE.match(line)
        if not match:
            i += 1
            continue

        speaker = normalize_whitespace(match.group("speaker"))
        timestamp = match.group("timestamp")
        inline_text = normalize_whitespace(match.group("text"))

        if inline_text:
            text = inline_text
            i += 1
        else:
            i += 1
            text_parts: list[str] = []
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    if text_parts:
                        break
                    continue
                if TRANSCRIPT_LINE_RE.match(next_line):
                    break
                text_parts.append(normalize_whitespace(next_line))
                i += 1
            text = normalize_whitespace(" ".join(text_parts))

        if text:
            segments.append(Segment(speaker=speaker, timestamp=timestamp, text=text))

    return segments


def merge_segments(segments: Iterable[Segment]) -> list[Segment]:
    merged: list[Segment] = []
    for seg in segments:
        if merged and merged[-1].speaker == seg.speaker:
            merged[-1].text = f"{merged[-1].text} {seg.text}".strip()
        else:
            merged.append(Segment(seg.speaker, seg.timestamp, seg.text))
    return merged


def extract_description_links(description: Optional[str]) -> list[tuple[str, str]]:
    if not description:
        return []
    return [(m.group("label").strip(), m.group("url").strip()) for m in DESCRIPTION_LINK_RE.finditer(description)]


def episode_url(meta: EpisodeMetadata, site_base: str) -> Optional[str]:
    base = site_base.rstrip("/")
    if meta.aliases:
        alias = meta.aliases[0].strip()
        if not alias.startswith("/"):
            alias = "/" + alias
        return f"{base}{alias}"
    if meta.episode:
        return f"{base}/{meta.episode}"
    return None


def youtube_url(youtube_id: Optional[str]) -> Optional[str]:
    return f"https://youtu.be/{youtube_id}" if youtube_id else None


def host_url(host_id: str, site_base: str) -> str:
    return f"{site_base.rstrip('/')}/host/{host_id}"


def parse_front_matter_title(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        front_matter_raw, _body = split_front_matter(raw)
        data = tomllib.loads(front_matter_raw)
        return _opt_str(data.get("title"))
    except Exception:
        return None


def resolve_host_name(repo_root: Path, host_id: str) -> str:
    host_path = repo_root / "content" / "host" / f"{host_id}.md"
    return parse_front_matter_title(host_path) or host_id


def resolve_guest_name(repo_root: Path, guest_id: str) -> str:
    guest_path = repo_root / "content" / "guest" / f"{guest_id}.md"
    return parse_front_matter_title(guest_path) or guest_id


def guest_url(guest_id: str, site_base: str) -> str:
    return f"{site_base.rstrip('/')}/guest/{guest_id}"


def escape_toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def default_blog_image(meta: EpisodeMetadata) -> str:
    if meta.episode:
        return f"img/episode/{meta.episode}/banner-{meta.episode}.webp"
    return "img/episode/default.jpg"


def default_images_value(meta: EpisodeMetadata) -> str:
    if meta.episode:
        return f"img/episode/{meta.episode}/banner-{meta.episode}.webp"
    return "img/episode/default-social.jpg"


def generate_short_description(meta: EpisodeMetadata) -> str:
    if meta.summary:
        text = normalize_whitespace(meta.summary)
        if len(text) <= 210:
            return text
        cut = text[:207].rsplit(" ", 1)[0].rstrip(",;: ")
        return f"{cut}..."
    parts: list[str] = []
    if meta.subtitle:
        parts.append(meta.subtitle)
    elif meta.title:
        parts.append(meta.title)
    topic_bits = []
    if meta.guests:
        topic_bits.append(f"with {', '.join(meta.guests)}")
    if meta.categories:
        topic_bits.append(f"on {', '.join(meta.categories[:3])}")
    if topic_bits:
        parts.append(" ".join(topic_bits))
    text = normalize_whitespace(". ".join(p for p in parts if p))
    return text or "Transcript of this Groong episode."


def split_into_paragraphs(text: str, max_chars: int, max_sentences: int) -> list[str]:
    text = normalize_whitespace(text)
    if not text:
        return []

    sentences = SENTENCE_SPLIT_RE.split(text)
    if len(sentences) <= 1 and len(text) <= max_chars:
        return [text]

    paragraphs: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        projected_len = current_len + (1 if current else 0) + len(sentence)
        if current and (len(current) >= max_sentences or projected_len > max_chars):
            paragraphs.append(" ".join(current).strip())
            current = [sentence]
            current_len = len(sentence)
        else:
            current.append(sentence)
            current_len = projected_len

    if current:
        paragraphs.append(" ".join(current).strip())

    return paragraphs or [text]


def render_front_matter(
    meta: EpisodeMetadata,
    transcript_title: str,
    description: str,
    blog_image: str,
    images_default: str,
    author: str,
    alias: str,
) -> str:
    date_value = format_toml_date(meta.date)
    publish_value = format_toml_date(meta.publish_date) or date_value
    lines = ["+++"]
    lines.append(f'Description = "{escape_toml_string(description)}"')
    if date_value:
        lines.append(f"Date = {date_value}")
    if publish_value:
        lines.append(
            'PublishDate = '
            f'{publish_value} # this is the datetime for the when the epsiode was published. '
            'This will default to Date if it is not set. Example is "2016-04-25T04:09:45-05:00"'
        )
    lines.append(f'title = "{escape_toml_string(transcript_title)}"')
    lines.append('#blog_banner = ""')
    lines.append(f'blog_image = "{escape_toml_string(blog_image)}"')
    lines.append(f'images = ["{escape_toml_string(images_default)}"]')
    if meta.categories:
        cats = ", ".join(f'"{escape_toml_string(c)}"' for c in meta.categories)
        lines.append(f"categories = [{cats}]")
    if meta.tags:
        tags = ", ".join(f'"{escape_toml_string(t)}"' for t in meta.tags)
        lines.append(f"tags = [{tags}]")
    lines.append('#Author = ""' if not author else f'Author = "{escape_toml_string(author)}"')
    lines.append('#aliases = ["/##"]' if not alias else f'aliases = ["{escape_toml_string(alias)}"]')
    lines.append("+++")
    return "\n".join(lines)


def render_body(
    meta: EpisodeMetadata,
    merged_segments: list[Segment],
    site_base: str,
    repo_root: Path,
    keep_timestamps: bool,
    max_paragraph_chars: int,
    max_paragraph_sentences: int,
) -> str:
    show_url = episode_url(meta, site_base)
    yt_url = youtube_url(meta.youtube_id)
    desc_links = extract_description_links(meta.description)

    parts: list[str] = []
    if meta.summary:
        parts.append(meta.summary.strip())

    parts.append("## Episode Information")
    info_lines: list[str] = []
    if meta.title:
        info_lines.append(f"- **Episode:** {meta.title}")
    if meta.subtitle:
        info_lines.append(f"- **Subtitle:** {meta.subtitle}")
    if meta.date:
        info_lines.append(f"- **Date:** {meta.date}")
    if meta.episode:
        info_lines.append(f"- **Episode Number:** {meta.episode}")
    if show_url:
        info_lines.append(f"- **Show Page:** [{show_url}]({show_url})")
    if yt_url:
        info_lines.append(f"- **YouTube:** [{yt_url}]({yt_url})")
    if meta.hosts:
        host_links = ", ".join(
            f"[{resolve_host_name(repo_root, host_id)}]({host_url(host_id, site_base)})"
            for host_id in meta.hosts
        )
        info_lines.append(f"- **Hosts:** {host_links}")
    if meta.guests:
        guest_links = ", ".join(
            f"[{resolve_guest_name(repo_root, guest_id)}]({guest_url(guest_id, site_base)})"
            for guest_id in meta.guests
        )
        info_lines.append(f"- **Guests:** {guest_links}")
    parts.append("\n".join(info_lines))

    if desc_links:
        parts.append("## Links")
        parts.append("\n".join(f"- [{label}]({url})" for label, url in desc_links))

    parts.append("## Transcript")
    parts.append("> **Warning:** This is a rush transcript generated automatically and may contain errors.")
    transcript_blocks: list[str] = []
    for seg in merged_segments:
        paragraphs = split_into_paragraphs(seg.text, max_paragraph_chars, max_paragraph_sentences)
        if not paragraphs:
            continue
        first = paragraphs[0]
        if keep_timestamps:
            block = [f"**{seg.speaker}** ({seg.timestamp}): {first}"]
        else:
            block = [f"**{seg.speaker}:** {first}"]
        block.extend(paragraphs[1:])
        transcript_blocks.append("\n\n".join(block))

    parts.append("\n\n".join(transcript_blocks))
    return "\n\n".join(part for part in parts if part.strip())




def build_default_output_path(repo_root: Path, meta: EpisodeMetadata, episode_path: Path) -> Path:
    date_prefix = format_toml_date(meta.publish_date) or format_toml_date(meta.date) or "undated"
    yyyymmdd = date_prefix.replace("-", "")
    episode_stem = episode_path.stem
    filename = f"{yyyymmdd}-transcript-{episode_stem}.md"
    return repo_root / "content" / "blog" / filename

def build_output(
    meta: EpisodeMetadata,
    merged_segments: list[Segment],
    site_base: str,
    repo_root: Path,
    keep_timestamps: bool,
    title_prefix: str,
    description: Optional[str],
    blog_image: Optional[str],
    images_default: Optional[str],
    author: str,
    alias: str,
    max_paragraph_chars: int,
    max_paragraph_sentences: int,
) -> str:
    transcript_title = f"{title_prefix}{meta.title}" if meta.title else "Transcript"
    front_matter = render_front_matter(
        meta,
        transcript_title,
        description=description or generate_short_description(meta),
        blog_image=blog_image or default_blog_image(meta),
        images_default=images_default or default_images_value(meta),
        author=author,
        alias=alias,
    )
    body = render_body(
        meta,
        merged_segments,
        site_base,
        repo_root,
        keep_timestamps,
        max_paragraph_chars,
        max_paragraph_sentences,
    )
    return f"{front_matter}\n\n{body}\n"


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    show_number = str(args.show_number).strip()

    try:
        transcript_path, episode_path = resolve_repo_files(repo_root, show_number)
    except (FileNotFoundError, FileExistsError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    meta = parse_episode_file(episode_path)
    segments = parse_transcript(transcript_path)
    if not segments:
        print(f"No transcript segments were parsed for episode {show_number}. Check the transcript format.", file=sys.stderr)
        return 1

    merged = merge_segments(segments)
    output = build_output(
        meta=meta,
        merged_segments=merged,
        site_base=args.site_base,
        repo_root=repo_root,
        keep_timestamps=args.keep_timestamps,
        title_prefix=args.title_prefix,
        description=args.description,
        blog_image=args.blog_image,
        images_default=args.images_default,
        author=args.author,
        alias=args.alias,
        max_paragraph_chars=args.max_paragraph_chars,
        max_paragraph_sentences=args.max_paragraph_sentences,
    )

    output_path = args.output or build_default_output_path(repo_root, meta, episode_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    print(f"Wrote {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
