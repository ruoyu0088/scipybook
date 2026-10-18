# -*- coding: utf-8 -*-
"""zh_style_tune.py — 中文版の文体指标を帯に寄せる。

zh_style_lint.py の measure() を真実として、1 ステップにつき 1 か所だけ直す:
  - 長すぎる文を読点で分割する(long が上限超え / sent_mean が高すぎる)
  - 短い文を隣と併合する(long が下限割れ / sent_mean が低すぎる / short が多すぎる)

段落構造は最後の手段(空行を消して 2〜3 段落を 1 文にする)だけ変える。

使い方:
    python tools/zh_style_tune.py <chapter-name> [--max-steps 40] [--dry-run]
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
LINT_PATH = Path(__file__).with_name("zh_style_lint.py")
CJK = re.compile(r"[\u4e00-\u9fff]")
SKIP_FIRST = set("#|>-*!<$`")
BAND = {"sent_mean": (27.0, 33.0), "short": (0.0, 0.10), "long": (0.10, 0.18)}


def load_lint():
    spec = importlib.util.spec_from_file_location("zh_style_lint", str(LINT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.argv, backup = ["zh_style_lint"], sys.argv
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = backup
    return mod


LINT = load_lint()


def is_para(line):
    s = line.strip()
    return bool(s) and s[0] not in SKIP_FIRST and not re.match(r"^\d+\.", s)


def split_sentence(s, floor=14):
    """読点で 2 つに割る。両側が floor 漢字以上、割った後が 45 未満に収まること。"""
    best = None
    for m in re.finditer("，", s):
        left, right = s[:m.start()], s[m.start() + 1:]
        l, r = len(CJK.findall(left)), len(CJK.findall(right))
        if l < floor or r < floor or l >= 45 or r >= 45:
            continue
        score = abs(l - r)
        if best is None or score < best[0]:
            best = (score, m.start())
    if best is None:
        return None
    i = best[1]
    return s[:i] + "。" + s[i + 1:]


def longest_splittable(nb):
    best = None
    for ci, cell in enumerate(nb.cells):
        if cell.cell_type != "markdown":
            continue
        for li, line in enumerate(cell.source.replace("\r\n", "\n").split("\n")):
            if not is_para(line):
                continue
            for s in re.split(r"(?<=[。！？])", line):
                if not s.strip() or len(CJK.findall(s)) < 45:
                    continue
                if split_sentence(s) is None:
                    continue
                n = len(CJK.findall(s))
                if best is None or n > best[3]:
                    best = (ci, li, s, n)
    return best


def shortest_mergeable(nb, allow_join_paragraphs=False):
    best = None
    for ci, cell in enumerate(nb.cells):
        if cell.cell_type != "markdown":
            continue
        lines = cell.source.replace("\r\n", "\n").split("\n")
        for li, line in enumerate(lines):
            if not is_para(line):
                continue
            sents = [s for s in re.split(r"(?<=[。！？])", line) if s.strip()]
            for k in range(len(sents) - 1):
                total = len(CJK.findall(sents[k])) + len(CJK.findall(sents[k + 1]))
                if total > 54:
                    continue
                if best is None or total < best[4]:
                    best = ("line", ci, li, k, total, None)
        if allow_join_paragraphs:
            for li in range(len(lines) - 2):
                a, blank, b = lines[li], lines[li + 1], lines[li + 2]
                if blank.strip() or not a.strip() or not b.strip():
                    continue
                if not is_para(a) or not is_para(b):
                    continue
                if not (a.strip().endswith("。") and b.strip().endswith("。")):
                    continue
                total = len(CJK.findall(a)) + len(CJK.findall(b))
                if not (45 <= total <= 84):
                    continue
                if best is None or total < best[4]:
                    best = ("para", ci, li, 0, total, None)
    return best


def triple_merge(nb):
    """3 段落を 1 文にまとめて長文を作る(短い章向け)。"""
    best = None
    for ci, cell in enumerate(nb.cells):
        if cell.cell_type != "markdown":
            continue
        lines = cell.source.replace("\r\n", "\n").split("\n")
        for li in range(len(lines) - 4):
            block = lines[li:li + 5]
            if block[1].strip() or block[3].strip():
                continue
            a, b, c = block[0].strip(), block[2].strip(), block[4].strip()
            if not (a and b and c):
                continue
            if not all(is_para(x) for x in (a, b, c)):
                continue
            if not all(x.endswith("。") for x in (a, b, c)):
                continue
            total = sum(len(CJK.findall(x)) for x in (a, b, c))
            if not (45 <= total <= 110):
                continue
            if best is None or total < best[4]:
                best = ("triple", ci, li, 0, total, None)
    return best


def apply_merge(nb, cand, crlf):
    kind, ci, li, k, _, _ = cand
    cell = nb.cells[ci]
    lines = cell.source.replace("\r\n", "\n").split("\n")
    if kind == "triple":
        merged = (lines[li].strip()[:-1] + "，" + lines[li + 2].strip()[:-1]
                  + "，" + lines[li + 4].strip())
        lines[li:li + 5] = [merged]
    elif kind == "para":
        lines[li:li + 3] = [lines[li].strip()[:-1] + "，" + lines[li + 2].strip()]
    else:
        sents = [s for s in re.split(r"(?<=[。！？])", lines[li]) if s.strip()]
        sents[k] = sents[k][:-1] + "，" + sents[k + 1]
        del sents[k + 1]
        lines[li] = "".join(sents)
    cell.source = "\n".join(lines).replace("\n", "\r\n" if crlf else "\n")


def apply_split(nb, cand, crlf):
    ci, li, s, _ = cand
    cell = nb.cells[ci]
    lines = cell.source.replace("\r\n", "\n").split("\n")
    lines[li] = lines[li].replace(s, split_sentence(s), 1)
    cell.source = "\n".join(lines).replace("\n", "\r\n" if crlf else "\n")


def save(nb, path, crlf):
    text = nbformat.writes(nb)
    with open(path, "wb") as fh:
        fh.write(text.replace("\n", "\r\n").encode("utf-8") if crlf else text.encode("utf-8"))


def pick_action(m):
    lo_l, hi_l = BAND["long"]
    lo_m, hi_m = BAND["sent_mean"]
    hi_s = BAND["short"][1]
    if m["long"] > hi_l or m["sent_mean"] > hi_m:
        return "split"
    if m["long"] < lo_l or m["sent_mean"] < lo_m or m["short"] > hi_s:
        return "merge"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter")
    ap.add_argument("--max-steps", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    name = args.chapter[:-6] if args.chapter.endswith(".ipynb") else args.chapter
    path = ROOT / "scipybook_cn" / (name + ".ipynb")
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    nb = nbformat.read(path, as_version=4)

    for step in range(args.max_steps):
        m = LINT.measure(str(path))
        action = pick_action(m)
        if action is None:
            print("[%s] in band at step %d: %s/%s/%s"
                  % (name, step, m["sent_mean"], m["short"], m["long"]))
            break
        if action == "split":
            cand = longest_splittable(nb)
            if cand is None:
                print("[%s] no splittable sentence left" % name)
                break
            apply_split(nb, cand, crlf)
        else:
            cand = (shortest_mergeable(nb)
                    or shortest_mergeable(nb, allow_join_paragraphs=True)
                    or triple_merge(nb))
            if cand is None:
                print("[%s] no mergeable pair left" % name)
                break
            apply_merge(nb, cand, crlf)
        if args.dry_run:
            print("step %d: %s -> %s/%s/%s"
                  % (step, action, m["sent_mean"], m["short"], m["long"]))
            break
        save(nb, path, crlf)

    m = LINT.measure(str(path))
    print("[%s] final: mean=%s short=%s long=%s para=%s"
          % (name, m["sent_mean"], m["short"], m["long"], m["para"]))
    return 0 if pick_action(m) is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
