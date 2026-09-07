from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator
from xml.sax.saxutils import escape

from funcs.build_output import BuildPaths
from funcs.parser import Post


PAGE_SIZE = 10
SITE_URL = "https://devneopark.github.io"


def paginate(items: list[Any], size: int) -> Iterator[tuple[int, list[Any]]]:
    if size <= 0:
        raise ValueError("페이지 크기는 0보다 커야 합니다.")
    for start in range(0, len(items), size):
        yield start // size + 1, items[start:start + size]


def group_posts_by_tag(posts: list[Post]) -> dict[str, list[Post]]:
    grouped: dict[str, list[Post]] = {}
    for post in posts:
        for tag in post.tags:
            grouped.setdefault(tag, []).append(post)
    return grouped


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_post_indexes(paths: BuildPaths, posts: list[Post]) -> None:
    base = paths.dist_assets_dir / "pages" / "posts"
    for page_number, page_posts in paginate(posts, PAGE_SIZE):
        _write_json(
            base / f"pages.{page_number}.json",
            [post.to_dict() for post in page_posts],
        )


def write_tag_indexes(paths: BuildPaths, posts_by_tag: dict[str, list[Post]]) -> None:
    base = paths.dist_assets_dir / "pages" / "tags"
    for tag, posts in sorted(posts_by_tag.items()):
        for page_number, page_posts in paginate(posts, PAGE_SIZE):
            _write_json(
                base / tag / f"pages.{page_number}.json",
                [post.to_dict() for post in page_posts],
            )


def write_tag_list(paths: BuildPaths, posts_by_tag: dict[str, list[Post]]) -> None:
    _write_json(
        paths.dist_assets_dir / "pages" / "tags" / "tags.json",
        {"tags": sorted(posts_by_tag)},
    )


def write_sitemap(paths: BuildPaths, posts: list[Post]) -> None:
    entries = [
        ("/", None),
        ("/posts.html", None),
        ("/tags.html", None),
        *((f"/posts/{post.seq}.html", post.posted_at) for post in posts),
    ]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, lastmod in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(SITE_URL + path)}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{escape(lastmod)}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (paths.dist_dir / "sitemap.xml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
