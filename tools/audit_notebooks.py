# -*- coding: utf-8 -*-
"""Audit notebooks before the jupyter-book gate.

Usage:
    python audit_notebooks.py <book_dir_or_nb> [more ...]

Reports, per file: cell counts, code cells with execution_count=None (outputs wiped by a rewrite),
code cells carrying an error output, empty code cells, whether an H1 exists, and MyST labels.
Exit code 1 when anything is wrong, so it can gate a batch.
"""
import glob
import os
import sys

import nbformat


def audit(paths):
    problems = 0
    for path in sorted(paths):
        nb = nbformat.read(path, as_version=4)
        try:
            nbformat.validate(nb)
        except Exception as exc:  # noqa: BLE001 - report, do not crash the batch
            print(f"{os.path.basename(path):30s} INVALID: {exc}")
            problems += 1
            continue

        code = [c for c in nb.cells if c.cell_type == "code"]
        unexecuted = [i for i, c in enumerate(nb.cells)
                      if c.cell_type == "code" and c.get("execution_count") is None]
        errors = [i for i, c in enumerate(nb.cells) if c.cell_type == "code"
                  for o in c.get("outputs", []) if o.output_type == "error"]
        empty = [i for i, c in enumerate(nb.cells)
                 if c.cell_type == "code" and not "".join(c.source).strip()]
        h1 = [line for c in nb.cells if c.cell_type == "markdown"
              for line in c.source.splitlines() if line.startswith("# ")]
        labels = [c.source.splitlines()[0] for c in nb.cells
                  if c.cell_type == "markdown" and c.source.startswith("(")]

        bad = unexecuted or errors or empty or not h1
        problems += bool(bad)
        print(f"{os.path.basename(path):30s} cells={len(nb.cells):3d} code={len(code):3d} "
              f"unexecuted={unexecuted} errors={errors} empty_code={empty} "
              f"h1={'yes' if h1 else 'MISSING'} labels={labels}")

    print("\nPROBLEMS:", problems or "none")
    return 1 if problems else 0


if __name__ == "__main__":
    targets = sys.argv[1:] or ["."]
    files = []
    for target in targets:
        if os.path.isdir(target):
            files.extend(glob.glob(os.path.join(target, "*.ipynb")))
        else:
            files.append(target)
    sys.exit(audit(files))
