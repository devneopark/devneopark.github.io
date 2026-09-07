from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from funcs import converter, html_generator
from funcs.parser import Post


ROBOTS_FILENAME = "robots.txt"
GOOGLE_VERIFICATION_FILENAME = "googleec3a32855dc9da2c.html"


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
        shutil.copy2(paths.assets_dir / filename, paths.dist_dir / filename)


def write_post_pages(paths: BuildPaths, template: str, posts: list[Post]) -> None:
    paths.dist_posts_dir.mkdir(parents=True, exist_ok=True)
    for post in posts:
        html_generator.generate_post(
            paths.dist_posts_dir / f"{post.seq}.html",
            template,
            converter.convert(post.body),
            post,
        )


def write_static_pages(paths: BuildPaths, template: str) -> None:
    home_body = converter.convert(
        (paths.assets_dir / "HOME.md").read_text(encoding="utf-8")
    )
    html_generator.generate_static(
        paths.dist_dir / "index.html", template, home_body, "Home"
    )
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
