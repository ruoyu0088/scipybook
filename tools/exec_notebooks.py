"""Execute notebooks in place and print every output (verification step of a chapter rewrite).

usage: python exec_notebooks.py <book_dir> <a.ipynb> [<b.ipynb> ...]

env: NB_KERNEL (default python3), NB_TIMEOUT (default 180 seconds)

Run with the environment python that must execute the book, e.g.
  C:/pixi_env/.pixi/envs/default/python.exe exec_notebooks.py <book_dir> z3_intro.ipynb

The kernel name resolves through that interpreter's own kernelspecs, so "python3" is the env's python.
Stops at the first cell error (allow_errors=False) and exits non-zero.
"""
import os
import sys

import nbformat
from nbclient import NotebookClient


def run(book_dir, name):
    path = os.path.join(book_dir, name)
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=int(os.environ.get("NB_TIMEOUT", "180")),
        kernel_name=os.environ.get("NB_KERNEL", "python3"),
        resources={"metadata": {"path": book_dir}},
        allow_errors=False,
    )
    client.execute()
    nbformat.write(nb, path)
    print("=" * 40)
    print("EXECUTED:", name)
    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        lines = []
        for out in cell.get("outputs", []):
            if out.output_type == "stream":
                lines.append("".join(out.text).rstrip())
            elif out.output_type == "execute_result":
                lines.append(str(out["data"].get("text/plain", "")))
            elif out.output_type == "error":
                lines.append("ERROR " + out.ename + ": " + out.evalue)
        print(f"--- cell {i} ---")
        print("\n".join(lines) if lines else "(no output)")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    book_dir = argv[0]
    for name in argv[1:]:
        run(book_dir, name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
