"""Regression tests for safely reusing published HTML in a print-focused fork.

Run with the same Python dependencies as print-book.py, for example:
uv run --python 3.12 --with beautifulsoup4==4.15.0 --with weasyprint==70.0 \
    python -m unittest discover -s scripts -p 'test_print_book.py'
"""

import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("print_book", Path(__file__).with_name("print-book.py"))
print_book = importlib.util.module_from_spec(spec)
spec.loader.exec_module(print_book)


class PublishedHtmlTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.run_git("init", "--quiet")
        for directory in ("book", "examples"):
            (self.root / directory).mkdir()
            (self.root / directory / "source.lean").write_text("-- original\n")
        (self.root / ".gitignore").write_text("book/_out/\n")
        self.commit()
        self.source = self.run_git("rev-parse", "HEAD")
        self.destination = self.root / "book/_out/print/site"
        self.responses = {
            "commits/gh-pages": json.dumps({
                "sha": "a" * 40,
                "commit": {"message": f"Book built from {self.source}"},
            }).encode(),
            f"git/trees/{self.source}": json.dumps({"tree": [
                {"path": path, "sha": self.run_git("rev-parse", f"HEAD:{path}")}
                for path in ("book", "examples")
            ]}).encode(),
            f"tarball/{'a' * 40}": self.archive("site/index.html", b"<html>Book</html>"),
        }
        self.addCleanup(patch.stopall)
        patch.object(print_book, "ROOT", self.root).start()
        patch.object(print_book, "github", side_effect=self.responses.__getitem__).start()

    def run_git(self, *args):
        return subprocess.check_output([
            "git", "-c", "user.name=Print tests", "-c", "user.email=print@example.com", *args,
        ], cwd=self.root, text=True).strip()

    def commit(self):
        self.run_git("add", ".")
        self.run_git("commit", "--quiet", "-m", "Test changes")

    def archive(self, name, contents, symlink=False):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
            member = tarfile.TarInfo(name)
            if symlink:
                member.type = tarfile.SYMTYPE
                member.linkname = "../../outside"
                tar.addfile(member)
            else:
                member.size = len(contents)
                tar.addfile(member, io.BytesIO(contents))
        return buffer.getvalue()

    def test_fork_commit_can_reuse_identical_book_sources(self):
        (self.root / "README.md").write_text("This fork adds printing.\n")
        self.commit()
        self.assertNotEqual(self.source, self.run_git("rev-parse", "HEAD"))
        site, revision = print_book.published_html(self.destination)
        self.assertEqual(revision, self.source)
        self.assertEqual((site / "index.html").read_text(), "<html>Book</html>")
        provenance = json.loads((site.parent / "source.json").read_text())
        self.assertEqual(provenance["source_commit"], self.source)
        self.assertEqual(provenance["checkout_commit"], self.run_git("rev-parse", "HEAD"))

    def test_rejects_committed_changes_to_book_or_examples(self):
        for directory in ("book", "examples"):
            with self.subTest(directory=directory):
                source = self.root / directory / "source.lean"
                source.write_text("-- changed\n")
                self.commit()
                with self.assertRaisesRegex(SystemExit, "does not match the book sources"):
                    print_book.published_html(self.destination)
                source.write_text("-- original\n")
                self.commit()

    def test_rejects_uncommitted_source_changes(self):
        (self.root / "book/source.lean").write_text("-- changed locally\n")
        with self.assertRaisesRegex(SystemExit, "local changes"):
            print_book.published_html(self.destination)

    def test_rejects_untracked_source_files(self):
        (self.root / "examples/new.lean").write_text("-- new example\n")
        with self.assertRaisesRegex(SystemExit, "local changes"):
            print_book.published_html(self.destination)

    def test_new_download_replaces_stale_html(self):
        self.destination.mkdir(parents=True)
        (self.destination / "old.html").write_text("old chapter")
        print_book.published_html(self.destination)
        self.assertFalse((self.destination / "old.html").exists())

    def test_rejects_archive_path_traversal_and_links(self):
        for name, symlink in (("site/../escape", False), ("site/link", True)):
            with self.subTest(name=name):
                self.responses[f"tarball/{'a' * 40}"] = self.archive(name, b"bad", symlink)
                with self.assertRaisesRegex(SystemExit, "Unexpected path"):
                    print_book.published_html(self.destination)
                self.assertFalse((self.root / "book/_out/print/escape").exists())


if __name__ == "__main__":
    unittest.main()
