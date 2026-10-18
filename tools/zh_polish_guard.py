#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中文版「只改表达」的机械校验（thinking_code 双语书）。

    python zh_polish_guard.py --baseline        # 改写前跑一次，存每格字数
    python zh_polish_guard.py [name.ipynb ...]  # 校验；不带参数 = 日语 _toc.yml 的全部章节

对日语正本：cell 结构、代码 token、标签、假名、标题/表格/列表/围栏骨架、
            inline code 与数学里的 ASCII 条目、结构指纹
对基线：     cell 数、每格字数比（只许变长，不许缩水到 92% 以下）

注意：本脚本不检查「」这类日语引号，也不核对正文数字；收工前自己 grep。
"""
from __future__ import annotations

import io
import json
import re
import sys
import tokenize
from pathlib import Path

import yaml

BOOK = Path("C:/Users/ruoyu/Documents/notebooks/scipybook")
JA, ZH = BOOK / "scipybook" / "scipybook", BOOK / "scipybook_cn"
BASELINE = Path(__file__).resolve().parent / "zh_baseline.json"


def _stem(name: str) -> str:
    return name[:-6] if name.endswith(".ipynb") else name


def ja_path_of(zh_name: str) -> Path:
    """中文版文件名不带 -jp 后缀，日语正本多数带。"""
    stem = _stem(zh_name)
    for cand in (stem + "-jp.ipynb", stem + ".ipynb"):
        if (JA / cand).exists():
            return JA / cand
    return JA / (stem + ".ipynb")


def zh_path_of(ja_name: str) -> Path:
    stem = _stem(ja_name)
    if stem.endswith("-jp"):
        stem = stem[:-3]
    return ZH / (stem + ".ipynb")


KANA = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
LABEL = re.compile(r"^\(([\w-]+)\)=\s*$", re.M)
INLINE = re.compile(r"`([^`\n]+)`")
MATH = re.compile(r"(?<!\\)\$([^$\n]+?)(?<!\\)\$")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")
HEAD = re.compile(r"^(#{1,6})\s", re.M)
ASCII = re.compile(r"^[\x20-\x7e]*$")

TOK_IGNORE = {tokenize.COMMENT, tokenize.NL, tokenize.ENCODING}
TOK_LITERAL = {tokenize.STRING}
if hasattr(tokenize, "FSTRING_MIDDLE"):
    TOK_LITERAL.add(tokenize.FSTRING_MIDDLE)


def load(path: Path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    return nb, [(c["cell_type"], "".join(c["source"])) for c in nb["cells"]]


def tokens(src: str):
    """token 流：注释丢弃，字符串归一，非 ASCII 名字归一（伪代码里的 → ← 也算）。"""
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in TOK_IGNORE:
                continue
            val = tok.string
            if tok.type in TOK_LITERAL:
                val = "<literal>"
            elif not ASCII.match(val):
                val = "<non-ascii>"
            out.append((tok.type, val))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return out


def code_fences(src: str) -> list[str]:
    """``` 围栏块正文；{directive} 开头的块（admonition / mermaid 等）整块跳过。"""
    out, cur, inblock, skip = [], [], False, False
    for line in src.split("\n"):
        if line.lstrip().startswith("```"):
            if not inblock:
                inblock = True
                skip = line.lstrip().lstrip("`").strip().startswith("{")
                cur = []
            else:
                inblock = False
                if not skip:
                    out.append("\n".join(cur).strip())
            continue
        if inblock:
            cur.append(line)
    return out


def skeleton(block: str) -> list[str]:
    """非 Python 围栏块的结构骨架：去掉 ← 之后的注记，只留 ASCII 字符。"""
    out = []
    for line in block.split("\n"):
        line = line.split("←")[0]
        out.append("".join(c for c in line if 0x21 <= ord(c) <= 0x7E).rstrip())
    return out


def fences_equal(a: list[str], b: list[str]) -> bool:
    """能按 Python 解析就比较 token（注释可译），否则比结构骨架。"""
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        tx, ty = tokens(x), tokens(y)
        if tx is not None and ty is not None and tx == ty:
            continue
        if skeleton(x) != skeleton(y):
            return False
    return True


def table_rows(src: str) -> int:
    return sum(1 for l in src.split("\n") if l.strip().startswith("|") and l.strip().endswith("|"))


def list_items(src: str) -> int:
    return sum(1 for l in src.split("\n") if re.match(r"^\s*([-*+]|\d+\.)\s", l))


def fingerprint(nb):
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    with_out = sum(1 for c in code if c.get("outputs"))
    disp = sum(1 for c in code for o in c.get("outputs", []) if o.get("output_type") == "display_data")
    return len(code), with_out, disp


def split_code(span_list):
    """inline code / 数学拆成 (纯 ASCII 条目, 其余条目数)：ASCII 必须逐字相同。"""
    ascii_ones = sorted(s for s in span_list if ASCII.match(s))
    return ascii_ones, len(span_list) - len(ascii_ones)


def check(name: str, base: dict, use_ja: bool = False):
    bad, warn = [], []
    ja_path, zh_path = ja_path_of(name), zh_path_of(name)
    if not zh_path.exists():
        return [f"中文版缺失: {zh_path}"], warn
    ja_nb, ja_cells = load(ja_path)
    zh_nb, zh_cells = load(zh_path)

    if len(ja_cells) != len(zh_cells):
        bad.append(f"cell 数不一致 ja={len(ja_cells)} zh={len(zh_cells)}")
    else:
        diff = [i for i, (a, b) in enumerate(zip(ja_cells, zh_cells)) if a[0] != b[0]]
        if diff:
            bad.append(f"cell 类型不一致: {diff[:10]}")

    hit = KANA.findall(zh_path.read_text(encoding="utf-8"))
    if hit:
        bad.append(f"出现假名: {sorted(set(hit))[:10]}")

    fp_ja, fp_zh = fingerprint(ja_nb), fingerprint(zh_nb)
    if fp_ja != fp_zh:
        bad.append(f"结构指纹 (代码格, 有输出, display) ja={fp_ja} zh={fp_zh}")

    if len(ja_cells) == len(zh_cells):
        for i, ((ka, sa), (kb, sb)) in enumerate(zip(ja_cells, zh_cells)):
            if ka == "code":
                ta, tb = tokens(sa), tokens(sb)
                if ta is None or tb is None:
                    bad.append(f"cell {i}: 语法错误")
                elif ta != tb:
                    bad.append(f"cell {i}: 代码逻辑不一致")
                continue
            ja_lab, zh_lab = set(LABEL.findall(sa)), set(LABEL.findall(sb))
            if ja_lab != zh_lab:
                bad.append(f"cell {i}: 标签 {ja_lab} / {zh_lab}")
            for key, extract in (("inline code", lambda s: sorted(INLINE.findall(s))),
                                 ("行内数学", lambda s: sorted(MATH.findall(s)))):
                a, b = split_code(extract(sa)), split_code(extract(sb))
                if a[0] != b[0]:
                    bad.append(f"cell {i}: {key} 的英文条目不同 {a[0]} / {b[0]}")
                if a[1] != b[1]:
                    bad.append(f"cell {i}: {key} 的中文条目数 {a[1]} -> {b[1]}")
            if not fences_equal(code_fences(sa), code_fences(sb)):
                bad.append(f"cell {i}: 围栏代码不一致")
            ha = [m.group(0) for m in HEAD.finditer(sa)]
            hb = [m.group(0) for m in HEAD.finditer(sb)]
            if ha != hb:
                bad.append(f"cell {i}: 标题结构 {len(ha)} -> {len(hb)}")
            if table_rows(sa) != table_rows(sb):
                bad.append(f"cell {i}: 表格行数 {table_rows(sa)} -> {table_rows(sb)}")
            if list_items(sa) != list_items(sb):
                bad.append(f"cell {i}: 列表项数 {list_items(sa)} -> {list_items(sb)}")
            if len(LINK.findall(sa)) != len(LINK.findall(sb)):
                bad.append(f"cell {i}: 链接数 {len(LINK.findall(sa))} -> {len(LINK.findall(sb))}")

    old = [len(s) for _, s in ja_cells] if use_ja else base.get(name)
    if old:
        if len(old) != len(zh_cells):
            bad.append(f"cell 数相对基线变化 {len(old)} -> {len(zh_cells)}")
        else:
            for i, ((_, src), olen) in enumerate(zip(zh_cells, old)):
                if not olen:
                    continue
                ratio = len(src) / olen
                # 日文与中文的字数不可直接比较（假名、助词多），从日文重译时下限放到 0.75，
                # 结构（标题/表格/列表/链接/inline code）另由上面的检查兜底。
                thr, warn_thr = (0.75, 0.85) if use_ja else (0.92, 1.55)
                if ratio < thr:
                    bad.append(f"cell {i}: 字数缩水 {olen} -> {len(src)} ({ratio:.2f})")
                elif use_ja and ratio < warn_thr:
                    warn.append(f"cell {i}: 比日文短得多 {olen} -> {len(src)} ({ratio:.2f})")
                elif ratio > 1.45:
                    warn.append(f"cell {i}: 字数膨胀 {olen} -> {len(src)} ({ratio:.2f})")
    else:
        warn.append("没有基线数据")
    return bad, warn


def names_from_toc() -> list[str]:
    toc = yaml.safe_load((JA / "_toc.yml").read_text(encoding="utf-8"))
    ja_names = [f"{c['file']}.ipynb" for p in toc.get("parts", []) for c in p.get("chapters", [])]
    return [zh_path_of(n).name for n in ja_names]


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--baseline":
        base = {}
        for n in names_from_toc():
            p = zh_path_of(n)
            if p.exists():
                _, cells = load(p)
                base[n] = [len(s) for _, s in cells]
        BASELINE.write_text(json.dumps(base, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"baseline written: {BASELINE} ({len(base)} files)")
        return 0

    base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}
    names = args or names_from_toc()
    use_ja = "--ja" in names
    if use_ja:
        # 从日文重译时，字数下限以日文原文为准（中文译文通常比日文短 0〜15%）
        names = [n for n in names if n != "--ja"] or names_from_toc()
        print("（字数基线 = 日文原文）")
    fails = 0
    for n in names:
        n = n if n.endswith(".ipynb") else n + ".ipynb"
        bad, warn = check(n, base, use_ja)
        print(f"{'FAIL' if bad else 'OK  '} {n}")
        for b in bad:
            print("     !!", b)
        for w in warn:
            print("     ..", w)
        fails += bool(bad)
    print(f"\n{len(names) - fails}/{len(names)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
