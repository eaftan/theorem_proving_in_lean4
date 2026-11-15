Theorem Proving in Lean 4
-----------------------

This repository contains the source code of the book _Theorem Proving
in Lean 4_ by Jeremy Avigad, Leonardo de Moura, Soonho Kong, and
Sebastian Ullrich, with contributions from the Lean Community.

**This fork adds a way to generate a printable PDF of the book.** The book comes
from [leanprover/theorem_proving_in_lean4](https://github.com/leanprover/theorem_proving_in_lean4);
the additions here are the PDF converter, print stylesheet, and printing
instructions. Read the [online edition](https://lean-lang.org/theorem_proving_in_lean4/)
for interactive examples and hover information.

**[Download the printable PDF](https://raw.githubusercontent.com/eaftan/theorem_proving_in_lean4/master/print/Theorem-Proving-in-Lean-4.pdf)**
(US Letter). The PDF is checked into this repository, so you can download it
without installing anything.

## Generate a printable PDF

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[WeasyPrint's system dependencies](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation).
The converter requires Python 3.12 or newer; `uv` manages Python and the pinned
Python dependencies automatically. Install DejaVu fonts as well for mathematical
symbols not covered by the fonts bundled with the book.

For example, on Ubuntu/Debian, install the system libraries and fallback fonts:

```sh
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core
```

From the repository root, run:

```sh
uv run --locked scripts/print-book.py --published
```

This downloads upstream's published HTML, without needing a Lean installation,
and creates **`print/Theorem-Proving-in-Lean-4.pdf`**. It also saves the combined
HTML alongside the PDF and writes `print/Theorem-Proving-in-Lean-4.json`, a
manifest recording the build inputs, document content, and PDF file hash.
The Letter PDF and its manifest are checked into Git; intermediate HTML and
other PDF filenames are ignored.

The PDF includes all chapters, a table of contents with page numbers, PDF
bookmarks, internal links, running chapter headers, code examples, displayed
output, and explicit proof states. Website navigation, copy buttons, hidden
example setup, and hover-only information are omitted. A licensing appendix
includes the full book license, attribution, and embedded-font notices, so the
PDF can be distributed by itself.

The download is checked against the contents of this checkout's `book/` and
`examples/` directories. Commits changing only the print tools or README are
fine; changes to the book sources require a local HTML build. Upstream's
published HTML must correspond to those sources, so a newer upstream publication
may also require updating the fork or building locally. The downloaded build's
source and HTML commit IDs are recorded in `book/_out/print/source.json`.

US Letter is the default. For A4 paper or a different output filename:

```sh
uv run --locked scripts/print-book.py --published --paper A4 --output print/book-a4.pdf
```

For a physical copy, print in black and white, double-sided, one PDF page per
side, at actual size (100%), and flip on the long edge. Coil/spiral binding lets
the book lie flat beside a computer. The margins leave room for binding.

## Build from local book sources

With [Lean installed](https://lean-lang.org/install/), build the examples and
HTML using the toolchain versions specified in the repository:

```sh
(cd examples && lake build && lake build subverso-extract-mod)
(cd book && lake exe tpil)
uv run --locked scripts/print-book.py
```

The default HTML input is `book/_out/html-multi`. To use another existing build:

```sh
uv run --locked scripts/print-book.py --html-dir path/to/html-multi
```

From the `book` directory, run `lake exe verso-serve` to view the HTML book.

## Implementation and maintenance

[`scripts/print-book.py`](scripts/print-book.py) combines Verso's chapter HTML
using Beautiful Soup, then renders it with WeasyPrint and
[`scripts/print-book.css`](scripts/print-book.css). Edit the stylesheet to adjust
fonts, spacing, margins, and page layout. The converter preserves the book's
prose and examples; the print layout is maintained in this fork.

Run the freshness and converter regression tests with:

```sh
python3 -m unittest discover -s scripts -p test_print_manifest.py
uv run --python 3.12 --with beautifulsoup4==4.15.0 --with weasyprint==70.0 \
  python -m unittest discover -s scripts -p test_print_book.py
```

The upstream authorship and [Apache 2.0 license](LICENSE) are retained. To bring
in future book updates from a clone of this fork:

```sh
git remote add upstream https://github.com/leanprover/theorem_proving_in_lean4.git
git fetch upstream
git merge upstream/master
```

Add the `upstream` remote only once.

### Keep the checked-in PDF current

CI runs on pushes to `master` and pull requests. It has two checks:

1. **Check checked-in PDF** verifies the manifest against the current book,
   examples, generator, stylesheet, locked Python dependencies, and license
   inputs, then verifies the PDF's hash. This needs only Python's standard
   library. Run it locally with `python3 scripts/print_manifest.py`.
2. **Build book** builds the fork's current sources with Lean, renders a fresh
   PDF from that local HTML, and compares its document-content fingerprint
   with the checked-in edition. This catches stale local HTML and changes to
   Verso's output as well as exercising PDF generation after upstream merges.

The comparison preserves code whitespace and compares prose, headings, tables,
and links. It uses content rather than PDF byte equality because different
Pango/FreeType versions can encode or lay out the same document differently.
The input fingerprint is printed on the title page. It describes relevant file
contents, rather than a Git commit ID, so committing the PDF or updating the
README does not immediately invalidate it.

After syncing upstream, regenerate the PDF and commit both files:

```sh
uv run --locked scripts/print-book.py --published
python3 scripts/print_manifest.py
git add print/Theorem-Proving-in-Lean-4.pdf print/Theorem-Proving-in-Lean-4.json
git commit -m "Update printable book"
```

If upstream's published HTML no longer matches, build locally as described
above, or use CI's **`printable-pdf`** artifact. CI uploads the freshly generated
PDF and manifest before comparing them with the checked-in version, so the
artifact is available even when the comparison reports a stale PDF. Download
it from the CI run on GitHub, or use the GitHub CLI with that run's ID:

```sh
gh run download RUN_ID --repo eaftan/theorem_proving_in_lean4 --name printable-pdf --dir print
python3 scripts/print_manifest.py
git add print/Theorem-Proving-in-Lean-4.pdf print/Theorem-Proving-in-Lean-4.json
git commit -m "Update printable book"
```

Use an artifact from the same source inputs you are committing. CI does not
commit generated files automatically. Review the PDF after updating, especially
after changes to Verso's HTML structure.

### PDF redistribution and licensing

The repository's Apache License 2.0 permits redistribution in source and object
form, including generated documentation and conversions to other media (see
sections 1, 2, and 4 of [LICENSE](LICENSE)). This edition preserves the authorship
and acknowledgments, identifies the print-format modifications, and includes
the complete license and any root `NOTICE*` files in its appendix. The repository
also retains the original license and attribution notices.

Source Serif 4 and Source Code Pro permit embedding under the SIL Open Font
License; their license texts are already present under `book/static/fonts/` and
are reproduced in the PDF. DejaVu fallback-font notices are preserved in
[`print/DejaVu-LICENSE.txt`](print/DejaVu-LICENSE.txt) and in the appendix.

