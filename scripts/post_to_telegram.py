"""
Post the latest article to a Telegram channel.

Env vars required:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- SITEURL (optional, default GitHub Pages URL)

Usage (in CI):
  python scripts/post_to_telegram.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests


def parse_metadata(md_path: Path) -> dict:
    metadata: dict[str, str] = {}
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            break
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip().lower()] = value.strip()
    return metadata


def latest_post() -> Path | None:
    posts = sorted(
        Path("content/posts").glob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return posts[0] if posts else None


def build_message(meta: dict, url: str) -> str:
    title = meta.get("title", "New post")
    summary = meta.get("summary", "")
    parts = [f"New post: {title}"]
    if summary:
        parts.append(summary)
    parts.append(url)
    return "\n".join(parts)


def main() -> int:
    if os.environ.get("SKIP_TELEGRAM") == "1":
        print("Skipping Telegram post (SKIP_TELEGRAM=1).")
        return 0

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    siteurl = os.getenv("SITEURL", "https://kmamaroziqov.github.io").rstrip("/")

    if not token or not chat_id:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID; aborting.", file=sys.stderr)
        return 1

    post_path = latest_post()
    if not post_path:
        print("No posts found in content/posts.")
        return 0

    meta = parse_metadata(post_path)
    slug = meta.get("slug", post_path.stem)
    link = meta.get("link") or f"{siteurl}/posts/{slug}/"

    message = build_message(meta, link)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": chat_id, "text": message},
        timeout=10,
    )

    if resp.status_code != 200:
        print(f"Telegram API error: {resp.status_code} {resp.text}", file=sys.stderr)
        return 1

    print(f"Posted to Telegram: {post_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
