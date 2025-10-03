def _render_tags_ul(tags):
    if not tags:
        return "<ul></ul>"
    items = []
    for t in tags:
        items.append(f"<li><a href='/tags.html?tag={t}'>#{t}</a></li>")
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def generate_post(html_path, html_template, body_html, meta: dict, jss: str = ""):
    template = html_template

    template = template.replace("${title}", meta["title"])
    head_tags = (
        f'<meta name="Date" content="{meta["posted_at"]}">\n'
        f'    <meta name="Keywords" content="{meta["title"]}">\n'
        f'    <meta name="Keywords" content="{meta["summary"]}">\n'
        f'    <meta name="Description" content="{meta["summary"]}">'
    )
    template = template.replace("${head.tags}", head_tags)

    template = template.replace("${jss}", jss or "")

    article_header = (
        f"<h1>{meta['title']}</h1>\n"
        f"{_render_tags_ul(meta.get('tags', []))}\n"
        f"<p>{meta['posted_at']}</p>"
    )
    template = template.replace("            ${article.header}", article_header)
    template = template.replace("                ${article.content}", body_html)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(template)


def generate_static(html_path, html_template, body, title, js_path: str):
    template = html_template
    template = template.replace("${head.tags}", "")
    template = template.replace("${title}", title)
    template = template.replace("${jss}", f"<script type='module' src='{js_path}'></script>" if js_path else "")
    template = template.replace("            ${article.header}", f"<h1>{title}</h1>")
    template = template.replace("                ${article.content}", body)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(template)
