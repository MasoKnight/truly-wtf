#!/usr/bin/env python3
"""
build.py — turns the markdown files in content/ into the static site in docs/.

Usage:
    python3 build.py

Workflow for a new post:
    1. Create content/posts/YYYY-MM-DD-some-slug.md
    2. Add frontmatter at the top (see any existing post for an example)
    3. Write the post in markdown below the frontmatter
    4. Run: python3 build.py
    5. git add, commit, push — GitHub Pages / Cloudflare picks up docs/

Nothing here needs to be touched to write a post. Only edit this file if
you want to change *how* the site is built (templates live in templates/,
the look lives in static/style.css).
"""

import re
import shutil
from datetime import datetime
from pathlib import Path

import markdown as md

# ---------------------------------------------------------------------------
# Site-wide settings. Edit these to taste.
# ---------------------------------------------------------------------------

SITE_TITLE = "Truly WTF?!"
SITE_TAGLINE = "A personal blog"
SITE_DESCRIPTION = "Notes on learning, pen testing, and figuring things out."
FOOTER_TEXT = f"&copy; {datetime.now().year} {SITE_TITLE}. Built from markdown."

# Your custom domain. Leave as "" if you don't want a CNAME file written.
DOMAIN = "truly.wtf"

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
POSTS_DIR = CONTENT / "posts"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUTPUT = ROOT / "docs"

MD_EXTENSIONS = ["extra", "sane_lists", "smarty"]

DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")


# ---------------------------------------------------------------------------
# Tiny frontmatter parser (no extra dependency beyond `markdown`)
# ---------------------------------------------------------------------------

def parse_frontmatter(text):
    """Split a markdown file into (metadata dict, body text).

    Frontmatter looks like:
        ---
        title: My Post
        date: 2026-09-15
        ---
        The rest is markdown.
    """
    meta = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            raw_meta, body = parts[1], parts[2]
            for line in raw_meta.strip().splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    meta[key.strip().lower()] = value.strip()
            return meta, body.lstrip("\n")
    return meta, text


def render_markdown(text):
    return md.markdown(text, extensions=MD_EXTENSIONS)


def fill(template_text, **kwargs):
    out = template_text
    for key, value in kwargs.items():
        out = out.replace("{{" + key + "}}", value)
    return out


def format_date(raw_date):
    if not raw_date:
        return None, None
    try:
        dt = datetime.strptime(raw_date, "%Y-%m-%d")
        return dt, dt.strftime("%d %B %Y")
    except ValueError:
        return None, raw_date


def slug_and_date_from_filename(path):
    stem = path.stem
    match = DATE_PREFIX_RE.match(stem)
    if match:
        return match.group(1), match.group(2)
    return None, stem


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def load_posts():
    posts = []
    if not POSTS_DIR.exists():
        return posts

    for path in sorted(POSTS_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body_md = parse_frontmatter(raw)

        filename_date, slug = slug_and_date_from_filename(path)
        raw_date = meta.get("date", filename_date)
        date_obj, date_display = format_date(raw_date)

        title = meta.get("title", slug.replace("-", " ").title())
        description = meta.get("description", "")

        posts.append({
            "slug": slug,
            "title": title,
            "description": description,
            "date_obj": date_obj,
            "date_display": date_display,
            "body_html": render_markdown(body_md),
        })

    # newest first; undated posts sink to the bottom, alphabetically
    dated = [p for p in posts if p["date_obj"] is not None]
    undated = [p for p in posts if p["date_obj"] is None]
    dated.sort(key=lambda p: p["date_obj"], reverse=True)
    undated.sort(key=lambda p: p["slug"])
    return dated + undated


def render_base(content_html, page_title, page_description, root):
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    return fill(
        base,
        page_title=page_title,
        page_description=page_description,
        content=content_html,
        root=root,
        site_title=SITE_TITLE,
        site_tagline=SITE_TAGLINE,
        footer_text=FOOTER_TEXT,
    )


def build_post_pages(posts):
    post_template = (TEMPLATES / "post.html").read_text(encoding="utf-8")

    for post in posts:
        meta_html = ""
        if post["date_display"]:
            meta_html = f'<p class="post-meta">{post["date_display"]}</p>'

        content = fill(
            post_template,
            title=post["title"],
            meta=meta_html,
            body=post["body_html"],
            root="../../",
        )

        page = render_base(
            content_html=content,
            page_title=f'{post["title"]} — {SITE_TITLE}',
            page_description=post["description"] or SITE_DESCRIPTION,
            root="../../",
        )

        out_dir = OUTPUT / "posts" / post["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(page, encoding="utf-8")


def build_home_page(posts):
    home_meta, home_body_md = parse_frontmatter(
        (CONTENT / "home.md").read_text(encoding="utf-8")
    )
    intro_html = render_markdown(home_body_md)

    items = []
    for post in posts:
        date_html = (
            f'<span class="post-date">{post["date_display"]}</span>'
            if post["date_display"]
            else ""
        )
        items.append(
            f'<li>{date_html}<a href="posts/{post["slug"]}/">{post["title"]}</a></li>'
        )

    home_template = (TEMPLATES / "home.html").read_text(encoding="utf-8")
    content = fill(
        home_template,
        intro=intro_html,
        post_list="\n".join(items) if items else "<li>No posts yet.</li>",
    )

    page = render_base(
        content_html=content,
        page_title=home_meta.get("title", SITE_TITLE),
        page_description=home_meta.get("description", SITE_DESCRIPTION),
        root="",
    )
    (OUTPUT / "index.html").write_text(page, encoding="utf-8")


def copy_static():
    (OUTPUT).mkdir(parents=True, exist_ok=True)
    shutil.copy(STATIC / "style.css", OUTPUT / "style.css")


def write_cname():
    if DOMAIN:
        (OUTPUT / "CNAME").write_text(DOMAIN + "\n", encoding="utf-8")


def main():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    copy_static()
    posts = load_posts()
    build_post_pages(posts)
    build_home_page(posts)
    write_cname()

    print(f"Built {len(posts)} post(s) into {OUTPUT}/")
    for post in posts:
        when = post["date_display"] or "(no date)"
        print(f"  - {when}: {post['title']}  ->  docs/posts/{post['slug']}/")


if __name__ == "__main__":
    main()
