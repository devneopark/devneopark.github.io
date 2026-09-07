import sys
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from funcs.parser import PostParseError, parse


class ParserTest(unittest.TestCase):
    def write_post(self, content: str) -> Path:
        directory = Path(tempfile.mkdtemp())
        path = directory / "00001-example.md"
        path.write_text(content, encoding="utf-8")
        self.addCleanup(lambda: shutil.rmtree(directory))
        return path

    def test_parse_normalizes_yaml_date_and_preserves_body(self):
        path = self.write_post(
            "---\n"
            "seq: 1\n"
            "title: 제목\n"
            "summary: 요약\n"
            "tags: [python, build]\n"
            "posted_at: 2026-09-07\n"
            "---\n"
            "\n"
            "본문입니다.\n"
        )

        post = parse(path)

        self.assertEqual(post.seq, 1)
        self.assertEqual(post.tags, ("python", "build"))
        self.assertEqual(post.posted_at, date(2026, 9, 7).isoformat())
        self.assertEqual(post.body, "본문입니다.")
        self.assertEqual(post.to_dict()["filename"], "00001-example.md")
        self.assertNotIn("body", post.to_dict())

    def test_parse_rejects_missing_required_metadata(self):
        path = self.write_post("---\nseq: 1\ntitle: 제목\n---\n본문\n")

        with self.assertRaisesRegex(PostParseError, "summary"):
            parse(path)

    def test_parse_rejects_file_without_front_matter(self):
        path = self.write_post("본문만 있습니다.")

        with self.assertRaises(PostParseError):
            parse(path)


if __name__ == "__main__":
    unittest.main()
