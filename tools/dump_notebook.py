"""Dump notebook cells compactly, with stored outputs, for reading a book chapter.

usage: python dump_notebook.py <a.ipynb> [<b.ipynb> ...] [--full]

Read-only. Handles nbformat v4 notebooks only (all jupyter-book v1 sources are v4).
"""
import json
import sys


def dump(path, full=False):
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    cells = nb.get("cells", [])
    print("=" * 30, path, "cells:", len(cells))
    print("kernelspec:", nb.get("metadata", {}).get("kernelspec"))
    for i, cell in enumerate(cells):
        src = "".join(cell.get("source", []))
        print(f"\n--- [{i}] {cell.get('cell_type')} ---")
        print(src if full else src[:1200])
        for out in cell.get("outputs", []):
            kind = out.get("output_type")
            if kind == "stream":
                text = "".join(out.get("text", []))
            elif kind in ("execute_result", "display_data"):
                text = str(out.get("data", {}).get("text/plain", ""))
            elif kind == "error":
                text = f"{out.get('ename')}: {out.get('evalue')}"
            else:
                continue
            body = text.rstrip()[:400].replace("\n", "\n  >> ")
            print("  >>", body)


def main(argv):
    full = "--full" in argv
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 1
    for path in paths:
        dump(path, full)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
