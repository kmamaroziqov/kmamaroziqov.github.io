from __future__ import annotations

import os

AUTHOR = "Kamronbek Mamaroziqov"
SITENAME = "My thoughts and notes on my Experiments"
SITESUBTITLE = "Thoughtful notes on AI and automation"
SITEURL = ""

PATH = "content"

TIMEZONE = "UTC"
DEFAULT_LANG = "en"

THEME = "themes/minimal"
THEME_STATIC_DIR = "theme"
THEME_STATIC_PATHS = ["static"]

ARTICLE_URL = "posts/{slug}/"
ARTICLE_SAVE_AS = "posts/{slug}/index.html"
PAGE_URL = "{slug}/"
PAGE_SAVE_AS = "{slug}/index.html"

DEFAULT_PAGINATION = 5
PAGINATED_TEMPLATES = {"index": None}

RELATIVE_URLS = True
MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.codehilite": {"css_class": "highlight"},
        "markdown.extensions.extra": {},
        "markdown.extensions.meta": {},
    },
    "output_format": "html5",
}

SOCIAL = (
    ("telegram", "https://t.me/personal_notebook"),
    ("linkedin", "https://www.linkedin.com/in/kmamaroziqov/"),
    ("github", "https://github.com/kmamaroziqov"),
)

FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

STATIC_PATHS = ["images", "extra/CNAME"]
EXTRA_PATH_METADATA = {
    "extra/CNAME": {"path": "CNAME"},
}

PLUGIN_PATHS = []
PLUGINS = []

# Convenience metadata for templates
SITE_META = {
    "telegram": os.environ.get("SITE_TELEGRAM", "https://t.me/personal_notebook"),
    "linkedin": os.environ.get("SITE_LINKEDIN", "https://www.linkedin.com/in/kmamaroziqov/"),
    "email": os.environ.get("SITE_EMAIL", "kmamaroziqov@gmail.com"),
}

JINJA_GLOBALS = {
    "CURRENT_YEAR": __import__("datetime").datetime.utcnow().year,
}
