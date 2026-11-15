"""Test PDF freshness and integrity without a renderer or network access."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import print_manifest


class ManifestTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git("init", "--quiet")
        for path in ("book/chapter.lean", "examples/example.lean", "LICENSE",
                     "scripts/print-book.py", "scripts/print-book.py.lock",
                     "scripts/print-book.css", "scripts/print_manifest.py",
                     "print/DejaVu-LICENSE.txt"):
            self.put(path, "original\n")
        self.put(".gitignore", "book/_out/\nbook/.verso/\n")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "Book sources")
        self.pdf = self.root / "print/book.pdf"
        self.pdf.write_bytes(b"%PDF-1.7\noriginal PDF bytes")
        self.source_inputs = print_manifest.inputs(self.root)
        self.content = print_manifest.sha256(b"rendered book content")
        self.record(self.pdf)

    def git(self, *args):
        return subprocess.check_output([
            "git", "-c", "user.name=Print tests", "-c", "user.email=print@example.com", *args,
        ], cwd=self.root, text=True).strip()

    def put(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def record(self, pdf, content=None):
        print_manifest.write(pdf, "Letter", self.source_inputs,
                             content or self.content, 1, self.root)

    def test_accepts_pdf_and_manifest_generated_from_current_inputs(self):
        result = print_manifest.check(self.pdf, root=self.root)
        self.assertEqual(result["pdf_sha256"], print_manifest.sha256(self.pdf.read_bytes()))
        self.assertEqual(result["source_commit"], self.git("rev-parse", "HEAD"))

    def test_unrelated_commit_does_not_require_pdf_regeneration(self):
        self.put("README.md", "How to download the PDF\n")
        self.git("add", "README.md")
        self.git("commit", "--quiet", "-m", "Document download")
        print_manifest.check(self.pdf, root=self.root)

    def test_rejects_changed_book_generator_stylesheet_or_dependencies(self):
        for path in ("book/chapter.lean", "examples/example.lean", "scripts/print-book.py",
                     "scripts/print-book.css", "scripts/print-book.py.lock", "LICENSE"):
            with self.subTest(path=path):
                self.put(path, "changed\n")
                with self.assertRaisesRegex(ValueError, "PDF is stale"):
                    print_manifest.check(self.pdf, root=self.root)
                self.put(path, "original\n")

    def test_rejects_new_chapter_or_notice(self):
        for path in ("book/new.lean", "NOTICE"):
            with self.subTest(path=path):
                self.put(path, "new input\n")
                with self.assertRaisesRegex(ValueError, "PDF is stale"):
                    print_manifest.check(self.pdf, root=self.root)
                (self.root / path).unlink()

    def test_rejects_deleted_input(self):
        (self.root / "book/chapter.lean").unlink()
        with self.assertRaisesRegex(ValueError, "PDF is stale"):
            print_manifest.check(self.pdf, root=self.root)

    def test_ignores_generated_html_and_examples(self):
        self.put("book/_out/index.html", "generated HTML")
        self.put("book/.verso/verso-xref-manifest.json", "generated cross-reference cache")
        self.put("examples/.gitignore", "Generated.lean\n")
        # Updating ignore rules is itself a book input change: record it first.
        self.source_inputs = print_manifest.inputs(self.root)
        self.record(self.pdf)
        self.put("examples/Generated.lean", "generated example")
        print_manifest.check(self.pdf, root=self.root)

    def test_rejects_altered_pdf(self):
        self.pdf.write_bytes(b"different PDF")
        with self.assertRaisesRegex(ValueError, "PDF bytes"):
            print_manifest.check(self.pdf, root=self.root)

    def test_rejects_input_fingerprint_tampering(self):
        path = self.pdf.with_suffix(".json")
        manifest = json.loads(path.read_text())
        manifest["input_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "input fingerprint"):
            print_manifest.check(self.pdf, root=self.root)

    def test_catches_sources_changing_during_generation(self):
        self.put("book/chapter.lean", "edited during rendering")
        with self.assertRaisesRegex(ValueError, "changed during generation"):
            self.record(self.pdf)

if __name__ == "__main__":
    unittest.main()
