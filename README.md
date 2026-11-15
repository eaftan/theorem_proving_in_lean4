Theorem Proving in Lean 4
-----------------------

This repository contains the source code of the book _Theorem Proving
in Lean 4_ by Jeremy Avigad, Leonardo de Moura, Soonho Kong, and
Sebastian Ullrich, with contributions from the Lean Community.

This fork provides a printable PDF edition of
[Theorem Proving in Lean 4](https://github.com/leanprover/theorem_proving_in_lean4).

**[Download the printable PDF](https://eaftan.github.io/theorem_proving_in_lean4/Theorem-Proving-in-Lean-4.pdf)** (US Letter).

For interactive examples and hover information,
[read the online edition](https://lean-lang.org/theorem_proving_in_lean4/).

## Printing

Print in black and white, double-sided, at actual size (100%), flipping on the
long edge. Spiral binding lets the book lie flat.

## Build your own PDF

Install [uv](https://docs.astral.sh/uv/getting-started/installation/),
[WeasyPrint's system dependencies](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation),
and DejaVu fonts. From the repository root, run:

```sh
uv run --locked scripts/print-book.py --published
```

The PDF is written to `print/Theorem-Proving-in-Lean-4.pdf`.
Add `--paper A4` to generate an A4 copy.

For modified book sources, follow
[upstream's HTML build instructions](https://github.com/leanprover/theorem_proving_in_lean4#readme),
then run the PDF command without `--published`.

To customize the print layout, edit [scripts/print-book.css](scripts/print-book.css).

## License

The book is licensed under [Apache 2.0](LICENSE). Font licenses are included in
the PDF.
