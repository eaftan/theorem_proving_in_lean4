#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["beautifulsoup4==4.15.0", "weasyprint==70.0"]
# ///
"""Make a paginated, printable book from Verso's multi-page HTML."""

import argparse
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
from urllib.error import URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from weasyprint import HTML


ROOT = Path(__file__).resolve().parent.parent
REPO = "leanprover/theorem_proving_in_lean4"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def github(path):
    request = Request(f"https://api.github.com/repos/{REPO}/{path}",
                      headers={"User-Agent": "tpil-print"})
    with urlopen(request, timeout=120) as response:
        return response.read()


def published_html(destination):
    """Only reuse a published build when it matches the local book source."""
    if git("status", "--porcelain", "--untracked-files=normal", "--", "book", "examples"):
        raise SystemExit("Book sources have local changes; build the HTML locally and use --html-dir.")
    commit = json.loads(github("commits/gh-pages"))
    match = re.fullmatch(r"Book built from ([0-9a-f]{40})", commit["commit"]["message"].strip())
    if not match:
        raise SystemExit("Cannot identify the source revision of the published HTML.")
    revision = match.group(1)
    source_tree = json.loads(github(f"git/trees/{revision}"))
    published = {entry["path"]: entry["sha"] for entry in source_tree["tree"]}
    # Compare content, not commit IDs: commits adding print tools or changing the
    # README in a fork should not prevent reuse of the upstream book build.
    for directory in ("book", "examples"):
        if git("rev-parse", f"HEAD:{directory}") != published.get(directory):
            raise SystemExit("Published HTML does not match the book sources; build locally and use --html-dir.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    archive = github(f"tarball/{commit['sha']}")
    with tempfile.TemporaryDirectory(dir=destination.parent) as staging:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            for member in tar.getmembers():
                parts = Path(member.name).parts[1:]
                if not parts:
                    continue
                if not (member.isfile() or member.isdir()) or ".." in parts:
                    raise SystemExit("Unexpected path in published HTML archive")
                member.name = str(Path(*parts))
                tar.extract(member, staging, filter="data")
        if not (Path(staging) / "index.html").is_file():
            raise SystemExit("Published archive does not contain index.html")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(staging, destination)
    (destination.parent / "source.json").write_text(json.dumps({
        "source_repository": REPO, "source_commit": revision,
        "html_commit": commit["sha"], "checkout_commit": git("rev-parse", "HEAD")},
        indent=2) + "\n", encoding="utf-8")
    return destination, revision


def parse(path):
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def clean(section):
    # Context used to compile examples and hover-only states are not book text.
    for tag in section.select(
        "script, .hidden, .hover-container, .tactic > .tactic-state, "
        ".permalink-widget, input, button, nav"):
        tag.decompose()
    # Plain monospace blocks print predictably, preserving indentation and output.
    for tag in section.select("code.block, pre"):
        text = tag.get_text().strip("\n")
        if not text.strip():
            tag.decompose()
            continue
        classes = ["output"] if "lean-output" in tag.get("class", []) else ["source-code"]
        tag.clear()
        tag.name = "pre"
        tag["class"] = classes
        tag.string = text
    for state in section.select(".proof-state-view"):
        for hypothesis in state.select(".hypothesis"):
            hypothesis.append("\n")
        for colon in state.select(".colon"):
            colon.string = " : "
        for label in state.select(".goal-name"):
            label.append("\n")
        for goal in state.select(".goal"):
            goal.append("\n")
        text = state.get_text().strip()
        state.clear()
        state.name = "pre"
        state["class"] = ["output", "proof-state"]
        state.string = text
    return section


def assemble(site, paper, revision):
    root = parse(site / "index.html")
    links = root.select("main .section-toc a")
    if not links:
        raise SystemExit("No chapters found in the Verso table of contents")
    book = BeautifulSoup("<!doctype html><html><head><meta charset='utf-8'>"
                         "<title>Theorem Proving in Lean 4</title>"
                         "<meta name='author' content='Jeremy Avigad; Leonardo de Moura; "
                         "Soonho Kong; Sebastian Ullrich'></head><body></body></html>", "html.parser")
    title = clean(root.select_one("main .titlepage"))
    title["class"] = ["titlepage"]
    title_heading = title.find("h1")
    title_heading.clear()
    title_heading.append("Theorem Proving")
    title_heading.append(book.new_tag("br"))
    title_heading.append("in Lean 4")
    note = book.new_tag("p", attrs={"class": "print-note"})
    note.string = (f"Print edition · {paper} · source {revision}\n"
                   "The online edition provides interactive examples and hover information.\n"
                   "https://lean-lang.org/theorem_proving_in_lean4/")
    title.append(note)
    book.body.append(title)
    toc = book.new_tag("div", attrs={"class": "print-toc"})
    heading = book.new_tag("h1")
    heading.string = "Contents"
    toc.append(heading)
    book.body.append(toc)
    targets = {}
    chapters = []
    for index, link in enumerate(links, 1):
        path = urlsplit(link["href"]).path
        section = clean(parse(site / path / "index.html").select_one("main .content-wrapper > section"))
        section["class"] = ["chapter"]
        # IDs can repeat between website pages. Prefix them before combining pages.
        for tag in section.select("[id]"):
            old = tag["id"]
            tag["id"] = f"ch{index}-{old}"
            targets[(path, old)] = tag["id"]
        h1 = section.find("h1")
        h1["id"] = f"chapter-{index}"
        targets[(path, unquote(urlsplit(link["href"]).fragment))] = h1["id"]
        targets[(path, "")] = h1["id"]
        for h in section.select("h1, h2"):
            if not h.get("id"):
                h["id"] = f"ch{index}-heading-{len(targets)}"
            entry = book.new_tag("a", href="#" + h["id"], attrs={
                "class": "toc-chapter" if h.name == "h1" else "toc-section"})
            entry.string = " ".join(h.get_text().split())
            toc.append(entry)
        chapters.append((path, section))
        book.body.append(section)
    for path, section in chapters:
        for link in section.select("a[href]"):
            url = urlsplit(link["href"])
            if url.scheme or url.netloc:
                continue
            key = (url.path or path, unquote(url.fragment))
            if key in targets:
                link["href"] = "#" + targets[key]
            else:
                link["href"] = "https://lean-lang.org/theorem_proving_in_lean4/" + link["href"]
    style = book.new_tag("style")
    css = (ROOT / "scripts" / "print-book.css").read_text(encoding="utf-8")
    style.string = css.replace("PAPER_SIZE", paper).replace(
        "FONT_ROOT", (ROOT / "book/static/fonts").as_uri())
    book.head.append(style)
    return str(book), len(chapters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--html-dir", type=Path, help="existing Verso HTML directory (default: book/_out/html-multi)")
    source.add_argument("--published", action="store_true", help="download upstream HTML if its book sources match this checkout")
    parser.add_argument("--paper", choices=["Letter", "A4"], default="Letter")
    parser.add_argument("--output", type=Path, default=ROOT / "print/Theorem-Proving-in-Lean-4.pdf")
    args = parser.parse_args()
    if args.output.suffix.lower() != ".pdf":
        parser.error("--output must have a .pdf extension")
    if args.published:
        try:
            site, revision = published_html(ROOT / "book/_out/print/site")
        except (URLError, OSError, tarfile.TarError, ValueError, KeyError) as error:
            parser.exit(1, f"Cannot download published HTML: {error}\n")
    else:
        site = (args.html_dir or ROOT / "book/_out/html-multi").resolve()
        revision = git("rev-parse", "HEAD")
    if not (site / "index.html").exists():
        parser.error("HTML not found; build the book first, or use --published")
    html, count = assemble(site, args.paper, revision[:7])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    html_path = args.output.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    document = HTML(string=html, base_url=str(site)).render()
    document.write_pdf(args.output)
    print(f"Created {args.output}: {count} chapters, {len(document.pages)} {args.paper} pages")


if __name__ == "__main__":
    main()
