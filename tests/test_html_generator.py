import sys
import shutil
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from funcs.html_generator import generate_post
from funcs.parser import Post


class HtmlGeneratorTest(unittest.TestCase):
    def test_generate_post_escapes_metadata_and_encodes_tag_query(self):
        template = (
            "<title>${title}</title>\n"
            "${head.tags}\n"
            "            ${article.header}\n"
            "                ${article.content}\n"
            "${jss}\n"
        )
        post = Post(
            seq=1,
            title="<제목>",
            summary='요약 "내용"',
            tags=("C++ & Python",),
            posted_at="2026-09-07",
            filename="post.md",
            body="본문",
        )
        output = Path(tempfile.mkdtemp()) / "post.html"
        self.addCleanup(lambda: shutil.rmtree(output.parent))

        generate_post(output, template, "<p>본문</p>", post)

        html = output.read_text(encoding="utf-8")
        self.assertIn("&lt;제목&gt;", html)
        self.assertIn("요약 &quot;내용&quot;", html)
        self.assertIn("/tags.html?tag=C%2B%2B+%26+Python", html)
        self.assertIn("<p>본문</p>", html)
        self.assertNotIn("${", html)


if __name__ == "__main__":
    unittest.main()
