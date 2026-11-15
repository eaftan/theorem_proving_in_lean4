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

**[Download the printable PDF](https://eaftan.github.io/theorem_proving_in_lean4/Theorem-Proving-in-Lean-4.pdf)**
(US Letter). CI generates the PDF and publishes it to GitHub Pages, so you can
download it without installing anything. The download serves the latest
successfully published build of `master`.

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
PDFs, manifests, and intermediate HTML are generated outputs and are ignored
by Git. The source code, print layout, and license notices stay in the repository.

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

Run the artifact-provenance and converter regression tests with:

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

### CI builds and GitHub Pages publication

CI builds the examples and book HTML from the fork's current sources, tests the
converter, then generates a fresh Letter PDF from that HTML. It verifies the
PDF's source-input fingerprint and file integrity, and uploads a
**`printable-pdf`** artifact containing the PDF and its JSON build manifest.
There is no checked-in PDF to regenerate or compare against.

After the build and provenance tests pass, builds of this fork's `master`
branch publish the generated PDF to GitHub Pages automatically. Pull requests
and release branches produce artifacts without publishing. Before deploying,
CI checks that the build still represents the latest `master` commit, so an
older in-flight build cannot overwrite a newer edition. If a build fails, the
previously published edition remains available.

The stable download is:

<https://eaftan.github.io/theorem_proving_in_lean4/Theorem-Proving-in-Lean-4.pdf>

The project root URL opens the PDF too. The JSON build manifest and license
notices are published alongside it. The manifest records the source commit,
input and document-content fingerprints, and PDF hash; the input fingerprint
also appears on the title page. Generated HTML, example files, and Verso's
cross-reference cache are excluded from the source-input fingerprint.

After syncing upstream, push the merge to `master`; CI rebuilds and publishes
the new edition. To request a fresh build manually, run the **CI** workflow
from GitHub Actions, or use:

```sh
gh workflow run ci.yml --repo eaftan/theorem_proving_in_lean4 --ref master
```

You can also download a CI artifact for local review without installing Lean
or the renderer. Use a run whose source inputs match your checkout:

```sh
gh run download RUN_ID --repo eaftan/theorem_proving_in_lean4 --name printable-pdf --dir print
python3 scripts/print_manifest.py
```

Pages is configured to deploy using **GitHub Actions** and the `github-pages`
environment. Publication is scoped to this fork in `.github/workflows/ci.yml`;
other forks can adapt the repository guard and URLs before enabling Pages in
their settings.

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

### Workflow dependencies

GitHub Actions use version tags, with direct and transitive action dependencies
locked in [`.github/workflows/actions.lock`](.github/workflows/actions.lock).
Generate this file with GitHub's CLI extension rather than editing it by hand:

```sh
gh extension install github/gh-actions-lock --pin v0.4.1
gh actions-lock
gh actions-lock --verify
```

Run the lock command after adding or changing action references, and commit the
workflow and lockfile changes together. The Lint workflow verifies coverage and
upstream pins. The existing Dependabot configuration keeps action versions and
their lockfile entries up to date. Docker images are outside the lockfile's
scope, so the actionlint image retains its digest pin.

