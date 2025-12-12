"""
Post new articles to Telegram channel.

Only posts if a NEW post file was added in the current commit.
Uses HTML parse mode for reliable formatting.

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


SENT_POSTS_FILE = Path(".telegram_sent_posts")


def load_sent_posts() -> set:
    """Load the set of post slugs that have already been sent to Telegram."""
    if SENT_POSTS_FILE.exists():
        return set(SENT_POSTS_FILE.read_text(encoding="utf-8").strip().split("\n"))
    return set()


def save_sent_post(slug: str):
    """Add a post slug to the sent posts file."""
    sent = load_sent_posts()
    sent.add(slug)
    SENT_POSTS_FILE.write_text("\n".join(sorted(sent)), encoding="utf-8")


def get_unsent_posts() -> list[Path]:
    """Get all posts that haven't been sent to Telegram yet."""
    sent_slugs = load_sent_posts()
    unsent = []
    
    posts_dir = Path("content/posts")
    if not posts_dir.exists():
        return []
    
    for post_file in posts_dir.glob("*.md"):
        # Get slug from file
        meta, _ = parse_metadata(post_file)
        slug = meta.get("slug", post_file.stem)
        
        if slug not in sent_slugs:
            unsent.append(post_file)
            print(f"Unsent post found: {post_file.name} (slug: {slug})")
        else:
            print(f"Already sent: {slug}")
    
    return unsent


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def convert_markdown_to_telegram_html(text: str) -> str:
    """Convert markdown to Telegram HTML format."""
    import re
    
    # Store code blocks temporarily
    code_blocks = []
    def save_code_block(match):
        code_blocks.append(f"<pre>{escape_html(match.group(2).strip())}</pre>")
        return f"__CODE_BLOCK_{len(code_blocks) - 1}__"
    
    text = re.sub(r'```(\w*)\n([\s\S]*?)```', save_code_block, text)
    
    # Store inline code
    inline_codes = []
    def save_inline_code(match):
        inline_codes.append(f"<code>{escape_html(match.group(1))}</code>")
        return f"__INLINE_{len(inline_codes) - 1}__"
    
    text = re.sub(r'`([^`]+)`', save_inline_code, text)
    
    # Escape HTML in remaining text
    text = escape_html(text)
    
    # Restore code blocks and inline code
    for i, block in enumerate(code_blocks):
        text = text.replace(f"__CODE_BLOCK_{i}__", block)
    for i, code in enumerate(inline_codes):
        text = text.replace(f"__INLINE_{i}__", code)
    
    # Convert markdown formatting
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    text = re.sub(r'(?<![*_])\*([^*]+)\*(?![*_])', r'<i>\1</i>', text)
    text = re.sub(r'(?<![*_])_([^_]+)_(?![*_])', r'<i>\1</i>', text)
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
    
    # Convert links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Remove images (keep alt text)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'🖼 \1', text)
    
    # Convert headers to bold
    text = re.sub(r'^#{1,6}\s+(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def build_message(meta: dict, body: str, url: str) -> str:
    title = meta.get("title", "New post")
    
    # Convert body to Telegram HTML
    telegram_body = convert_markdown_to_telegram_html(body)
    
    # Build message with HTML formatting
    parts = [
        f"<b>{escape_html(title)}</b>",
        "",
        telegram_body,
        "",
        f'🔗 <a href="{url}">Read more</a>',
        "",
        "@lab_log"
    ]
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

    # Get posts that haven't been sent to Telegram yet
    unsent_posts = get_unsent_posts()
    
    if not unsent_posts:
        print("No unsent posts found. Skipping Telegram.")
        return 0
    
    # Post all unsent posts (usually just one)
    for post_path in unsent_posts:
        print(f"Posting: {post_path.name}")
        
        meta, body = parse_metadata(post_path)
        slug = meta.get("slug", post_path.stem)
        link = meta.get("link") or f"{siteurl}/posts/{slug}/"

        message = build_message(meta, body, link)
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            },
            timeout=10,
        )

        if resp.status_code != 200:
            print(f"Telegram API error: {resp.status_code} {resp.text}", file=sys.stderr)
            return 1

        # Mark as sent
        save_sent_post(slug)
        print(f"Posted to Telegram: {post_path.name} (slug: {slug})")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
