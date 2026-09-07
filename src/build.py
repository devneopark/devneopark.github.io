from __future__ import annotations

from pathlib import Path

from funcs import index_generator, parser
from funcs.build_output import (
    BuildPaths,
    clean_generated_output,
    copy_assets,
    write_post_pages,
    write_static_pages,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_site(project_root: Path = PROJECT_ROOT) -> None:
    paths = BuildPaths.from_project_root(project_root)
    template = (paths.assets_dir / "template.html").read_text(encoding="utf-8")
    posts = parser.load_posts(paths.posts_dir)
    posts_by_tag = index_generator.group_posts_by_tag(posts)

    clean_generated_output(paths)
    copy_assets(paths)
    write_post_pages(paths, template, posts)
    index_generator.write_post_indexes(paths, posts)
    index_generator.write_tag_indexes(paths, posts_by_tag)
    index_generator.write_tag_list(paths, posts_by_tag)
    index_generator.write_sitemap(paths, posts)
    write_static_pages(paths, template)


def main() -> None:
    print("build started.")
    build_site()
    print("build done.")


if __name__ == "__main__":
    main()
