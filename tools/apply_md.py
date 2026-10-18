#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把新的 markdown 文本写回 notebook，保持原格式（indent=1, CRLF, 键序）。

    python apply_md.py <notebook.ipynb> <edits.json>

edits.json 形如 {"12": "整格新的 markdown 文本"}，键是 cell 下标。
只允许改 markdown 格；某格字数比原文少 8% 以上时拒绝写入（防止删内容）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print(__doc__)
        return 1
    nb_path, edits_path = Path(sys.argv[1]), Path(sys.argv[2])
    fresh = "--fresh" in sys.argv   # 从日文重译：字数下限交给 zh_polish_guard --ja
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    edits = json.loads(edits_path.read_text(encoding="utf-8"))

    old = {}
    for key, text in edits.items():
        i = int(key)
        cell = nb["cells"][i]
        if cell["cell_type"] != "markdown":
            print(f"拒绝: cell {i} 不是 markdown（{cell['cell_type']}）")
            return 1
        prev = "".join(cell["source"])
        if not fresh and len(text) < len(prev) * 0.92:
            print(f"拒绝: cell {i} 字数缩水 {len(prev)} -> {len(text)}")
            return 1
        old[i] = len(prev)
        lines = text.rstrip("\n").split("\n")
        cell["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]

    out = json.dumps(nb, ensure_ascii=False, indent=1)
    nb_path.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    for i in sorted(old):
        print(f"cell {i:>3}: {old[i]:>5} -> {len(edits[str(i)]):>5} chars")
    print(f"written: {nb_path} ({len(edits)} cell(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
