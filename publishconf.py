from __future__ import annotations

import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *  # noqa: F401,F403

SITEURL = os.environ.get("SITEURL", "https://kmamaroziqov.github.io")
RELATIVE_URLS = False

FEED_ALL_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = "feeds/{author}.atom.xml"
AUTHOR_FEED_RSS = None

DELETE_OUTPUT_DIRECTORY = True
