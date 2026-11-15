"""Record PDF build inputs and check that the distributed PDF is current.

The checker uses only Python's standard library; it does not need Lean or a PDF
renderer. The full book CI also compares a fresh build's document content.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF = ROOT / "print/Theorem-Proving-in-Lean-4.pdf"
INPUT_PATHS = (
    "book", "examples", "LICENSE", "NOTICE*", "COPYING*",
    "scripts/print-book.py", "scripts/print-book.py.lock",
    "scripts/print-book.css", "scripts/print_manifest.py",
    "print/DejaVu-LICENSE.txt",
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def inputs(root=ROOT):
    """Hash tracked and new source files, excluding ignored build products."""
    names = subprocess.check_output([
        "git", "ls-files", "-z", "--cached", "--others", "--exclude-standard",
        "--", *INPUT_PATHS,
    ], cwd=root).decode().split("\0")
    return {name: sha256((root / name).read_bytes()) for name in sorted(set(names))
            if name and (root / name).is_file()}


def fingerprint(source_inputs, paper):
    return sha256(json.dumps({"inputs": source_inputs, "paper": paper},
                             sort_keys=True, separators=(",", ":")).encode())


def write(pdf, paper, source_inputs, content_hash, pages, root=ROOT):
    if inputs(root) != source_inputs:
        raise ValueError("PDF inputs changed during generation; run the generator again.")
    manifest = {
        "schema": 1,
        "paper": paper,
        "input_sha256": fingerprint(source_inputs, paper),
        "inputs": source_inputs,
        "content_sha256": content_hash,
        "pdf_sha256": sha256(pdf.read_bytes()),
        "pages": pages,
    }
    pdf.with_suffix(".json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check(pdf, paper="Letter", root=ROOT):
    manifest = json.loads(pdf.with_suffix(".json").read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or manifest.get("paper") != paper:
        raise ValueError("PDF manifest has the wrong format or paper size.")
    current = inputs(root)
    recorded = manifest["inputs"]
    if not isinstance(recorded, dict):
        raise ValueError("PDF manifest inputs must be a filename-to-hash mapping.")
    changed = [name for name in sorted(current.keys() | recorded.keys())
               if current.get(name) != recorded.get(name)]
    if changed:
        raise ValueError("PDF is stale. Changed inputs: " + ", ".join(changed[:10]))
    if manifest["input_sha256"] != fingerprint(current, paper):
        raise ValueError("PDF input fingerprint does not match its manifest.")
    if manifest["pdf_sha256"] != sha256(pdf.read_bytes()):
        raise ValueError("PDF bytes do not match their manifest; regenerate the PDF.")
    return manifest


def compare(pdf, fresh_pdf, paper="Letter", root=ROOT):
    manifest = check(pdf, paper, root)
    fresh = check(fresh_pdf, paper, root)
    if manifest["content_sha256"] != fresh["content_sha256"]:
        raise ValueError("PDF content differs from the freshly built book; regenerate it.")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--paper", choices=("Letter", "A4"), default="Letter")
    parser.add_argument("--against", type=Path, help="compare with a fresh PDF build's content manifest")
    args = parser.parse_args()
    try:
        if args.against:
            manifest = compare(args.pdf, args.against, args.paper)
        else:
            manifest = check(args.pdf, args.paper)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"{error}\nRegenerate and commit the PDF together with its .json manifest.\n")
    print(f"PDF is current: {args.pdf} (inputs {manifest['input_sha256'][:12]})")


if __name__ == "__main__":
    main()
