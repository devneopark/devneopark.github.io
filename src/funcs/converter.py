from markdown import markdown

def convert(md_content: str) -> str:
    return markdown(md_content, extensions=["fenced_code"])
