import json
import os
import shutil

import funcs.parser
import funcs.converter
import funcs.html_generator

ASSETS_DIR = "_assets"
POSTS_DIR = "_posts"
DIST_DIR = "dist"
DIST_ASSETS_DIR = os.path.join(DIST_DIR, "assets")
PAGE_SIZE = 10

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def ensure_dir(path: str) -> None:
    if not path:
        return
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise FileExistsError(f"{path} exists and is not a directory")
        return
    os.makedirs(path, exist_ok=True)
#     os.makedirs(path, exist_ok=True)


def list_files(dir_path: str):
    return sorted(
        f for f in os.listdir(dir_path)
        if os.path.isfile(os.path.join(dir_path, f))
    )

def paginate(items, size: int):
    n = len(items)
    i = 0
    page = 1
    while i < n:
        yield page, items[i:i + size]
        i += size
        page += 1

def write_json(path: str, data) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def copy_assets_clean() -> None:
    if os.path.exists(DIST_ASSETS_DIR):
        shutil.rmtree(DIST_ASSETS_DIR)
    shutil.copytree(ASSETS_DIR, DIST_ASSETS_DIR)
    tpl_path = os.path.join(DIST_ASSETS_DIR, "template.html")
    if os.path.exists(tpl_path):
        os.remove(tpl_path)

def build_post_pages(html_template: str):
    posts_meta = []
    tags_map = {}

    for filename in list_files(POSTS_DIR):
        meta, body = funcs.parser.parse(os.path.join(POSTS_DIR, filename))
        meta["filename"] = filename

        body_html = funcs.converter.convert(body)
        html_path = os.path.join(DIST_DIR, "posts", str(meta["seq"]), "index.html")
        ensure_dir(os.path.dirname(html_path))
        funcs.html_generator.generate_post(
            html_path, html_template, body_html, meta, jss=""
        )

        posts_meta.append(meta)

        for tag in meta.get("tags", []):
            if tag not in tags_map:
                tags_map[tag] = []
            tags_map[tag].append(meta)

    return posts_meta, tags_map

def write_posts_index_pages(all_posts_meta):
    base = os.path.join(DIST_ASSETS_DIR, "pages", "posts")
    for page_no, chunk in paginate(all_posts_meta, PAGE_SIZE):
        path = os.path.join(base, f"pages.{page_no}.json")
        write_json(path, chunk)

def write_tag_index_pages(tags_map):
    base = os.path.join(DIST_ASSETS_DIR, "pages", "tags")
    for tag, metas in tags_map.items():
        for page_no, chunk in paginate(metas, PAGE_SIZE):
            path = os.path.join(base, tag, f"pages.{page_no}.json")
            write_json(path, chunk)

def write_tags_list_file(tags_map):
    tags = sorted(tags_map.keys())
    path = os.path.join(DIST_ASSETS_DIR, "pages", "tags", "tags.json")
    write_json(path, {"tags": tags})

def build_static_pages(html_template: str):
    home_md_path = os.path.join(ASSETS_DIR, "HOME.md")
    home_md = read_text(home_md_path)
    home_body = funcs.converter.convert(home_md)
    funcs.html_generator.generate_static(
        os.path.join(DIST_DIR, "index.html"),
        html_template,
        home_body,
        "Home",
        ""
    )

    funcs.html_generator.generate_static(
        os.path.join(DIST_DIR, "posts", "index.html"),
        html_template,
        "",
        "Posts",
        "/assets/js/posts.mjs"
    )

    ensure_dir(os.path.join(DIST_DIR, "tags"))
    funcs.html_generator.generate_static(
        os.path.join(DIST_DIR, "tags", "index.html"),
        html_template,
        "",
        "Tags",
        "/assets/js/tags.posts.mjs"
    )

def main():
    print("build started.")
    ensure_dir(DIST_DIR)

    html_template = read_text(os.path.join(ASSETS_DIR, "template.html"))

    posts_meta, tags_map = build_post_pages(html_template)
    posts_meta = list(reversed(posts_meta))

    tags_map = {
        tag: sorted(metas, key=lambda m: m["seq"], reverse=True)
        for tag, metas in tags_map.items()
    }

    copy_assets_clean()

    write_posts_index_pages(posts_meta)
    write_tag_index_pages(tags_map)
    write_tags_list_file(tags_map)

    build_static_pages(html_template)

    print("build done.")

if __name__ == "__main__":
    main()
