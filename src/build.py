from __future__ import annotations

import json
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from xml.sax.saxutils import escape

from funcs import converter, html_generator, parser
from funcs.parser import Post


PAGE_SIZE = 10
SITE_URL = "https://devneopark.github.io"
ROBOTS_FILENAME = "robots.txt"
GOOGLE_VERIFICATION_FILENAME = "googleec3a32855dc9da2c.html"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class BuildPaths:
    project_root: Path
    assets_dir: Path
    posts_dir: Path
    dist_dir: Path
    dist_assets_dir: Path
    dist_posts_dir: Path

    @classmethod
    def from_project_root(cls, project_root: Path) -> "BuildPaths":
        dist_dir = project_root / "dist"
        return cls(
            project_root=project_root,
            assets_dir=project_root / "_assets",
            posts_dir=project_root / "_posts",
            dist_dir=dist_dir,
            dist_assets_dir=dist_dir / "assets",
            dist_posts_dir=dist_dir / "posts",
        )


def paginate(items: list[Any], size: int) -> Iterator[tuple[int, list[Any]]]:
    if size <= 0:
        raise ValueError("페이지 크기는 0보다 커야 합니다.")
    for start in range(0, len(items), size):
        yield start // size + 1, items[start:start + size]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_posts(paths: BuildPaths) -> list[Post]:
    posts = [parser.parse(path) for path in sorted(paths.posts_dir.glob("*.md"))]
    duplicates = sorted(seq for seq, count in Counter(post.seq for post in posts).items() if count > 1)
    if duplicates:
        raise ValueError(f"중복된 포스트 seq가 있습니다: {duplicates}")
    return sorted(posts, key=lambda post: post.seq, reverse=True)


def group_posts_by_tag(posts: list[Post]) -> dict[str, list[Post]]:
    grouped: dict[str, list[Post]] = {}
    for post in posts:
        for tag in post.tags:
            grouped.setdefault(tag, []).append(post)
    return grouped


def clean_generated_output(paths: BuildPaths) -> None:
    paths.dist_dir.mkdir(parents=True, exist_ok=True)
    for directory in (paths.dist_assets_dir, paths.dist_posts_dir):
        if directory.exists():
            shutil.rmtree(directory)

    generated_files = (
        "index.html",
        "posts.html",
        "tags.html",
        "sitemap.xml",
        ROBOTS_FILENAME,
        GOOGLE_VERIFICATION_FILENAME,
    )
    for filename in generated_files:
        path = paths.dist_dir / filename
        if path.exists():
            path.unlink()


def copy_assets(paths: BuildPaths) -> None:
    shutil.copytree(paths.assets_dir, paths.dist_assets_dir)
    template_path = paths.dist_assets_dir / "template.html"
    if template_path.exists():
        template_path.unlink()

    for filename in (ROBOTS_FILENAME, GOOGLE_VERIFICATION_FILENAME):
        source = paths.assets_dir / filename
        destination = paths.dist_dir / filename
        shutil.copy2(source, destination)


def write_post_pages(paths: BuildPaths, template: str, posts: list[Post]) -> None:
    paths.dist_posts_dir.mkdir(parents=True, exist_ok=True)
    for post in posts:
        body_html = converter.convert(post.body)
        html_generator.generate_post(
            paths.dist_posts_dir / f"{post.seq}.html",
            template,
            body_html,
            post,
        )


def write_posts_index_pages(paths: BuildPaths, posts: list[Post]) -> None:
    base = paths.dist_assets_dir / "pages" / "posts"
    for page_number, page_posts in paginate(posts, PAGE_SIZE):
        write_json(
            base / f"pages.{page_number}.json",
            [post.to_dict() for post in page_posts],
        )


def write_tag_index_pages(
    paths: BuildPaths,
    posts_by_tag: dict[str, list[Post]],
) -> None:
    base = paths.dist_assets_dir / "pages" / "tags"
    for tag, posts in sorted(posts_by_tag.items()):
        for page_number, page_posts in paginate(posts, PAGE_SIZE):
            write_json(
                base / tag / f"pages.{page_number}.json",
                [post.to_dict() for post in page_posts],
            )


def write_tags_list_file(paths: BuildPaths, posts_by_tag: dict[str, list[Post]]) -> None:
    write_json(
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
    (paths.dist_dir / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_static_pages(paths: BuildPaths, template: str) -> None:
    home_body = converter.convert((paths.assets_dir / "HOME.md").read_text(encoding="utf-8"))
    html_generator.generate_static(paths.dist_dir / "index.html", template, home_body, "Home")
    html_generator.generate_static(
        paths.dist_dir / "posts.html",
        template,
        "",
        "Posts",
        "/assets/js/posts.mjs",
    )
    html_generator.generate_static(
        paths.dist_dir / "tags.html",
        template,
        "",
        "Tags",
        "/assets/js/tags.posts.mjs",
    )


def build_site(project_root: Path = PROJECT_ROOT) -> None:
    paths = BuildPaths.from_project_root(project_root)
    template = (paths.assets_dir / "template.html").read_text(encoding="utf-8")
    posts = load_posts(paths)
    posts_by_tag = group_posts_by_tag(posts)

    clean_generated_output(paths)
    copy_assets(paths)
    write_post_pages(paths, template, posts)
    write_posts_index_pages(paths, posts)
    write_tag_index_pages(paths, posts_by_tag)
    write_tags_list_file(paths, posts_by_tag)
    write_sitemap(paths, posts)
    write_static_pages(paths, template)


def main() -> None:
    print("build started.")
    build_site()
    print("build done.")


if __name__ == "__main__":
    main()
