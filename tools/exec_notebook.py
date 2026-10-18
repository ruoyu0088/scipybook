#!/usr/bin/env python3
"""在本地执行 notebook 并把输出写回（scipybook 用）。

用法:
    python tools/exec_notebook.py scipybook/numpy-ndarray-jp.ipynb [more.ipynb ...]

必须用 C:\\pixi_env 的 python 3.14 运行（NumPy/SciPy/matplotlib/bokeh/pyvista 都在里面）。

写回规则：
- 删掉 nbclient 塞进 cell metadata 的 execution 时间戳（否则每次执行都多出无意义的 diff）
- 保持文件原来的行尾（CRLF / LF），避免整份文件 diff 变噪音
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

# graphviz(dot.exe) は pixi 環境の Library/bin にあり、PATH には入っていない。
# helper.awkward.dot() が Graphviz を呼ぶので、実行時だけ PATH に足す。
_ENV_BIN = Path(sys.executable).resolve().parent / "Library" / "bin"
if _ENV_BIN.exists():
    os.environ["PATH"] = str(_ENV_BIN) + os.pathsep + os.environ.get("PATH", "")



def _write_like(original_bytes: bytes, nb, path: Path) -> None:
    text = nbformat.writes(nb, version=4)
    if text.endswith("\n"):
        text = text[:-1]
    if b"\r\n" in original_bytes:
        path.write_bytes(text.replace("\n", "\r\n").encode("utf-8") + b"\r\n")
    else:
        path.write_bytes(text.encode("utf-8") + b"\n")


def run(path: Path) -> bool:
    original = path.read_bytes()
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=1800,
        kernel_name="python3",
        resources={"metadata": {"path": str(path.parent)}},
        allow_errors=False,
    )
    try:
        client.execute()
    except Exception:
        failing = None
        for i, cell in enumerate(nb.cells):
            if cell.cell_type != "code":
                continue
            for out in cell.get("outputs", []):
                if out.get("output_type") == "error":
                    failing = (i, out.get("ename"), out.get("evalue"))
                    break
            if failing:
                break
        if failing:
            i, ename, evalue = failing
            head = nb.cells[i].source.splitlines()[0][:70]
            print(f"  [{path.name}] FAILED at cell {i}: {head}")
            print(f"    {ename}: {evalue}")
        raise
    for cell in nb.cells:
        cell.get("metadata", {}).pop("execution", None)
    _write_like(original, nb, path)

    errors = 0
    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        for out in cell.get("outputs", []):
            if out.get("output_type") == "error":
                errors += 1
                print(f"  [{path.name}] cell {i}: {out.get('ename')}: {out.get('evalue')}")
    unexecuted = [i for i, c in enumerate(nb.cells)
                  if c.cell_type == "code" and c.get("execution_count") is None]
    print(f"{'OK  ' if errors == 0 else 'FAIL'} {path} ({len(nb.cells)} cells)"
          + (f"  unexecuted={unexecuted}" if unexecuted else ""))
    return errors == 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    ok = True
    for arg in sys.argv[1:]:
        ok = run(Path(arg).resolve()) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
