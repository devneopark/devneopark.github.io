from __future__ import annotations

from html import escape
from pathlib import Path
from urllib.parse import urlencode

from funcs.parser import Post


def _render_tags(tags: tuple[str, ...]) -> str:
    if not tags:
        return "<ul></ul>"

    items = []
    for tag in tags:
        label = escape(tag)
        query = urlencode({"tag": tag})
        items.append(f"<li><a href='/tags.html?{query}'>#{label}</a></li>")
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def _replace_template(template: str, **values: str) -> str:
    for placeholder, value in values.items():
        template = template.replace(placeholder, value)
    return template


def generate_post(
    html_path: str | Path,
    html_template: str,
    body_html: str,
    post: Post,
) -> None:
    safe_title = escape(post.title)
    safe_summary = escape(post.summary, quote=True)
    safe_posted_at = escape(post.posted_at, quote=True)
    head_tags = (
        f'<meta name="date" content="{safe_posted_at}">\n'
        f'    <meta name="keywords" content="{safe_title}">\n'
        f'    <meta name="keywords" content="{safe_summary}">\n'
        f'    <meta name="description" content="{safe_summary}">'
    )
    article_header = (
        f"<h1>{safe_title}</h1>\n"
        f"{_render_tags(post.tags)}\n"
        f"<p>{escape(post.posted_at)}</p>"
    )
    html = _replace_template(
        html_template,
        **{
            "${title}": safe_title,
            "${head.tags}": head_tags,
            "${jss}": "",
            "            ${article.header}": article_header,
            "                ${article.content}": body_html,
        },
    )
    Path(html_path).write_text(html, encoding="utf-8")


def generate_static(
    html_path: str | Path,
    html_template: str,
    body_html: str,
    title: str,
    js_path: str = "",
) -> None:
    html = _replace_template(
        html_template,
        **{
            "${head.tags}": "",
            "${title}": escape(title),
            "${jss}": (
                f"<script type='module' src='{escape(js_path, quote=True)}'></script>"
                if js_path
                else ""
            ),
            "            ${article.header}": f"<h1>{escape(title)}</h1>",
            "                ${article.content}": body_html,
        },
    )
    Path(html_path).write_text(html, encoding="utf-8")
