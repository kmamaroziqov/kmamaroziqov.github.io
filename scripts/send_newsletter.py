"""
Send the latest article to Buttondown subscribers.

Env vars required:
- BUTTONDOWN_API_KEY
- SITEURL (optional, default GitHub Pages URL)

Usage (in CI):
  python scripts/send_newsletter.py
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


def main() -> int:
    if os.environ.get("SKIP_NEWSLETTER") == "1":
        print("Skipping newsletter (SKIP_NEWSLETTER=1).")
        return 0

    api_key = os.getenv("BUTTONDOWN_API_KEY")
    siteurl = os.getenv("SITEURL", "https://yourusername.github.io").rstrip("/")

    if not api_key:
        print("Missing BUTTONDOWN_API_KEY; aborting.", file=sys.stderr)
        return 1

    post_path = latest_post()
    if not post_path:
        print("No posts found in content/posts.")
        return 0

    meta = parse_metadata(post_path)
    slug = meta.get("slug", post_path.stem)
    link = meta.get("link") or f"{siteurl}/posts/{slug}/"
    subject = meta.get("title", "New post")
    summary = meta.get("summary", "")

    body = f"{summary}\n\nRead it here: {link}"

    resp = requests.post(
        "https://api.buttondown.email/v1/emails",
        headers={"Authorization": f"Token {api_key}"},
        json={"subject": subject, "body": body},
        timeout=10,
    )

    if resp.status_code >= 300:
        print(f"Buttondown API error: {resp.status_code} {resp.text}", file=sys.stderr)
        return 1

    print(f"Queued newsletter for: {post_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
