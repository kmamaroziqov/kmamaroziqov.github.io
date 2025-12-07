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


def parse_metadata(md_path: Path) -> tuple[dict, str]:
    """Parse frontmatter metadata and return (metadata, body content)."""
    metadata: dict[str, str] = {}
    lines = md_path.read_text(encoding="utf-8").splitlines()
    body_start = 0
    
    for i, line in enumerate(lines):
        if not line.strip():
            body_start = i + 1
            break
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip().lower()] = value.strip()
    
    body = "\n".join(lines[body_start:]).strip()
    return metadata, body


def latest_post() -> Path | None:
    posts = sorted(
        Path("content/posts").glob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return posts[0] if posts else None


def convert_markdown_to_telegram(text: str) -> str:
    """Convert markdown to Telegram-friendly format."""
    import re
    
    # Convert headers to bold
    text = re.sub(r'^### (.+)$', r'*\1*', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'*\1*', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'*\1*', text, flags=re.MULTILINE)
    
    # Convert bold **text** to *text*
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)
    
    # Convert links [text](url) to text (url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', text)
    
    # Convert images to alt text with URL
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'🖼 \1: \2', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text


def build_message(meta: dict, body: str, url: str) -> str:
    title = meta.get("title", "New post")
    
    # Convert body to Telegram format
    telegram_body = convert_markdown_to_telegram(body)
    
    # Build full message
    parts = [f"*{title}*", "", telegram_body, "", f"🔗 {url}", "", "@lab_log"]
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

    meta, body = parse_metadata(post_path)
    slug = meta.get("slug", post_path.stem)
    link = meta.get("link") or f"{siteurl}/posts/{slug}/"

    message = build_message(meta, body, link)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
        timeout=10,
    )

    if resp.status_code != 200:
        print(f"Telegram API error: {resp.status_code} {resp.text}", file=sys.stderr)
        return 1

    print(f"Posted to Telegram: {post_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
