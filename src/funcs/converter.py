from markdown import Markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor


class StrikethroughExtension(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r"(~{2})(.+?)(~{2})", "del"),
            "strikethrough",
            175,
        )

def convert(md_content: str) -> str:
    return Markdown(extensions=["fenced_code", StrikethroughExtension()]).convert(md_content)
