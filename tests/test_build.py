import shutil
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import build
from funcs import index_generator, parser
from funcs.build_output import BuildPaths


PROJECT_ROOT = Path(__file__).parents[1]


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.project_root))
        shutil.copytree(PROJECT_ROOT / "_assets", self.project_root / "_assets")
        shutil.copytree(PROJECT_ROOT / "_posts", self.project_root / "_posts")

    def test_build_creates_pages_and_removes_stale_generated_files(self):
        stale_posts = self.project_root / "dist" / "posts"
        stale_assets = self.project_root / "dist" / "assets"
        stale_posts.mkdir(parents=True)
        stale_assets.mkdir(parents=True)
        (stale_posts / "old.html").write_text("old", encoding="utf-8")
        (stale_assets / "old.json").write_text("old", encoding="utf-8")

        build.build_site(self.project_root)

        self.assertTrue((self.project_root / "dist/index.html").exists())
        self.assertTrue((self.project_root / "dist/posts/5.html").exists())
        self.assertTrue((self.project_root / "dist/sitemap.xml").exists())
        self.assertFalse((self.project_root / "dist/posts/old.html").exists())
        self.assertFalse((self.project_root / "dist/assets/old.json").exists())

    def test_paginate_rejects_invalid_page_size(self):
        with self.assertRaises(ValueError):
            list(index_generator.paginate([1], 0))

    def test_load_posts_rejects_duplicate_sequence_numbers(self):
        posts_dir = self.project_root / "_posts"
        (posts_dir / "duplicate.md").write_text(
            "---\n"
            "seq: 5\n"
            "title: 중복\n"
            "summary: 중복\n"
            "tags: [test]\n"
            "posted_at: 2026-09-07\n"
            "---\n"
            "본문\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "중복된 포스트 seq"):
            parser.load_posts(BuildPaths.from_project_root(self.project_root).posts_dir)


if __name__ == "__main__":
    unittest.main()
