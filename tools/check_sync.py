#!/usr/bin/env python3
"""双语 notebook 同步检查器与同步提示生成器（scipybook 版）。

日语正本: scipybook/scipybook/*.ipynb      （多数文件名带 -jp 后缀）
中文版本: scipybook_cn/*.ipynb             （文件名去掉 -jp 后缀）

用法:
    python tools/check_sync.py                      # 检查全部
    python tools/check_sync.py numpy-ndarray        # 只检查一个（给中文版文件名即可）
    python tools/check_sync.py --prompt numpy-ndarray   # 生成给 AI 的同步提示
    python tools/check_sync.py --update-state       # 同步完成后记录状态
    python tools/check_sync.py --update-toc         # 由日语版生成中文版 _toc.yml
    python tools/check_sync.py --strict             # 有问题时返回退出码 1

判定规则（两边都可以改）:
    日语改了、中文没改  → 提示 日语 → 中文
    中文改了、日语没改  → 提示 中文 → 日语
    两边都改了          → 冲突，需要合并
    状态文件缺失        → unknown，建议先 --update-state 建立基准
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tokenize
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
JA_DIR = ROOT / "scipybook" / "scipybook"
ZH_DIR = ROOT / "scipybook_cn"
STATE_PATH = ZH_DIR / ".sync_state.json"

KANA = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
LABEL = re.compile(r"^\(([\w-]+)\)=\s*$", re.M)

TOK_IGNORE = {tokenize.COMMENT, tokenize.NL, tokenize.ENCODING}
TOK_LITERAL = {tokenize.STRING}
if hasattr(tokenize, "FSTRING_MIDDLE"):
    TOK_LITERAL.add(tokenize.FSTRING_MIDDLE)


# ---------------------------------------------------------------- 文件名映射
def _stem(name: str) -> str:
    return name[:-6] if name.endswith(".ipynb") else name


def ja_name(zh_stem: str) -> str:
    """中文版文件名 → 日语正本文件名（多数带 -jp）。"""
    stem = _stem(zh_stem)
    for cand in (stem + "-jp", stem):
        if (JA_DIR / f"{cand}.ipynb").exists():
            return cand
    return stem


def zh_name(ja_stem: str) -> str:
    stem = _stem(ja_stem)
    return stem[:-3] if stem.endswith("-jp") else stem


def ja_path(name: str) -> Path:
    return JA_DIR / f"{ja_name(name)}.ipynb"


def zh_path(name: str) -> Path:
    return ZH_DIR / f"{zh_name(name)}.ipynb"


# ---------------------------------------------------------------- helpers
def load_cells(path: Path) -> list[tuple[str, str]]:
    nb = nbformat.read(path, as_version=4)
    return [(c.cell_type, "".join(c.source) if isinstance(c.source, list) else c.source)
            for c in nb.cells]


def cell_hash(src: str) -> str:
    return hashlib.sha1(src.encode("utf-8")).hexdigest()[:12]


def labels_of(cells) -> set[str]:
    found = set()
    for kind, src in cells:
        if kind == "markdown":
            found |= set(LABEL.findall(src))
    return found


def kana_count(cells) -> list[int]:
    return [i for i, (kind, src) in enumerate(cells) if KANA.search(src)]


def token_stream(src: str):
    """代码格的 token 流：忽略注释，字符串字面量归一化，非 ASCII 名字归一化。"""
    toks = []
    ascii_re = re.compile(r"^[\x20-\x7e]*$")
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in TOK_IGNORE:
                continue
            if tok.type in TOK_LITERAL:
                toks.append((tok.type, "<literal>"))
            elif not ascii_re.match(tok.string):
                toks.append((tok.type, "<non-ascii>"))
            else:
                toks.append((tok.type, tok.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return toks


def fingerprint(path: Path) -> tuple[int, int, int]:
    """(代码格数, 有输出的代码格数, display_data 数) —— 被清空或只跑一半的 notebook 靠它抓。"""
    nb = nbformat.read(path, as_version=4)
    code = [c for c in nb.cells if c.cell_type == "code"]
    with_out = sum(1 for c in code if c.get("outputs"))
    disp = sum(1 for c in code for o in c.get("outputs", [])
               if o.get("output_type") == "display_data")
    return len(code), with_out, disp


def read_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def write_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")


def changed_indices(new: list[str], old: list[str]) -> list[int]:
    n = max(len(new), len(old))
    return [i for i in range(n)
            if (new[i] if i < len(new) else None) != (old[i] if i < len(old) else None)]


def toc_stems() -> list[str]:
    """日语版 _toc.yml 中列出的全部章节（日语名）。"""
    import yaml

    data = yaml.safe_load((JA_DIR / "_toc.yml").read_text(encoding="utf-8"))
    files = []
    for part in data.get("parts", []):
        files += [c["file"] for c in part.get("chapters", [])]
    return files


def notebook_names(filter_name: str | None = None) -> list[str]:
    """以日语版 _toc.yml 为准；toc 之外的文件不处理。返回中文版文件名。"""
    allowed = toc_stems()
    names = sorted(f"{zh_name(n)}.ipynb" for n in allowed)
    if filter_name:
        wanted = zh_name(_stem(filter_name))
        names = [n for n in names if _stem(n) == wanted]
    return names


# ---------------------------------------------------------------- check
def analyse(name: str, state: dict) -> dict:
    """name 用中文版文件名；内部映射到日语正本。"""
    jp, zp = ja_path(name), zh_path(name)
    info = {"name": name, "ja": jp.exists(), "zh": zp.exists(),
            "problems": [], "direction": "unknown", "ja_changed": [], "zh_changed": [],
            "token_mismatch": [], "miss_labels": [], "kana": [], "fingerprint": None}

    if not info["ja"]:
        info["problems"].append(f"日语版缺失: {jp.name}")
        return info
    if not info["zh"]:
        info["problems"].append("中文版缺失（未翻译）")
        info["direction"] = "ja→zh"
        return info

    ja_cells, zh_cells = load_cells(jp), load_cells(zp)
    info["ja_cells"], info["zh_cells"] = len(ja_cells), len(zh_cells)
    info["files"] = (jp.name, zp.name)

    if len(ja_cells) != len(zh_cells):
        info["problems"].append(f"cell 数不一致: ja {len(ja_cells)} / zh {len(zh_cells)}")
    else:
        diff = [i for i, (a, b) in enumerate(zip(ja_cells, zh_cells)) if a[0] != b[0]]
        if diff:
            info["problems"].append(f"cell 类型不一致: {diff[:10]}")

    ja_labels, zh_labels = labels_of(ja_cells), labels_of(zh_cells)
    info["labels"] = (len(ja_labels), len(zh_labels))
    miss = ja_labels - zh_labels
    if miss:
        info["miss_labels"] = sorted(miss)
        info["problems"].append(f"中文版缺少标签: {sorted(miss)}")

    info["kana"] = kana_count(zh_cells)
    if info["kana"]:
        info["problems"].append(f"中文版出现假名: cell {info['kana'][:10]}")

    fp_ja, fp_zh = fingerprint(jp), fingerprint(zp)
    info["fingerprint"] = (fp_ja, fp_zh)
    if fp_ja != fp_zh:
        info["problems"].append(f"结构指纹 (代码格, 有输出, display) ja={fp_ja} zh={fp_zh}")

    if len(ja_cells) == len(zh_cells):
        for i, ((kind_a, src_a), (kind_b, src_b)) in enumerate(zip(ja_cells, zh_cells)):
            if kind_a != "code":
                continue
            ta, tb = token_stream(src_a), token_stream(src_b)
            if ta is None or tb is None:
                info["problems"].append(f"cell {i}: 语法错误，无法比较")
            elif ta != tb:
                info["token_mismatch"].append(i)
        if info["token_mismatch"]:
            info["problems"].append(f"代码逻辑不一致: {info['token_mismatch'][:10]}")

    entry = state.get(name)
    if not entry:
        info["direction"] = "unknown"
    else:
        ja_new = [cell_hash(s) for _, s in ja_cells]
        zh_new = [cell_hash(s) for _, s in zh_cells]
        jc = changed_indices(ja_new, entry.get("ja", []))
        zc = changed_indices(zh_new, entry.get("zh", []))
        info["ja_changed"], info["zh_changed"] = jc, zc
        if jc and zc:
            info["direction"] = "conflict"
        elif jc:
            info["direction"] = "ja→zh"
        elif zc:
            info["direction"] = "zh→ja"
        else:
            info["direction"] = "synced"
    return info


def print_report(results: list[dict]) -> None:
    mark = {"synced": "OK  ", "ja→zh": "JA> ", "zh→ja": "ZH> ",
            "conflict": "!!  ", "unknown": "??  "}
    for r in results:
        head = f"{mark[r['direction']]}{r['name']}"
        if "ja_cells" in r:
            head += f"  cells ja/zh = {r['ja_cells']}/{r['zh_cells']}"
            head += f"  labels = {r['labels'][0]}/{r['labels'][1]}"
            head += f"  kana = {len(r['kana'])}"
        print(head)
        if r["direction"] not in ("synced", "unknown"):
            if r["ja_changed"]:
                print(f"      日语侧改动: {r['ja_changed'][:15]}")
            if r["zh_changed"]:
                print(f"      中文侧改动: {r['zh_changed'][:15]}")
        for p in r["problems"]:
            print(f"      - {p}")


# ---------------------------------------------------------------- prompt
def first_line(src: str, limit: int = 60) -> str:
    for line in src.splitlines():
        line = line.strip()
        if line:
            return line[:limit] + ("…" if len(line) > limit else "")
    return "(空)"


def build_prompt(r: dict) -> str:
    name = r["name"]
    jp, zp = ja_path(name), zh_path(name)
    direction = r["direction"]
    if direction == "ja→zh":
        src_label, dst_label = "日语 → 中文", "日语版更新了"
    elif direction == "zh→ja":
        src_label, dst_label = "中文 → 日语", "中文版更新了"
    elif direction == "conflict":
        src_label, dst_label = "两边都改过（需要合并）", "冲突"
    else:
        src_label, dst_label = "未知（没有同步基准）", "请先比较全文"

    ja_cells = load_cells(jp) if jp.exists() else []
    zh_cells = load_cells(zp) if zp.exists() else []

    lines = ["【同步任务】scipybook 日/中双语 notebook",
             f"对象：{name}    方向：{src_label}（{dst_label}）", "",
             f"日语：{jp}", f"中文：{zp}", "", "变化摘要："]
    changed = sorted(set(r["ja_changed"]) | set(r["zh_changed"]))
    if changed:
        for i in changed[:20]:
            src = (ja_cells[i][1] if i < len(ja_cells) else "") or (zh_cells[i][1] if i < len(zh_cells) else "")
            kind = ja_cells[i][0] if i < len(ja_cells) else "?"
            side = []
            if i in r["ja_changed"]:
                side.append("日语")
            if i in r["zh_changed"]:
                side.append("中文")
            lines.append(f"- cell {i}  {kind}  {'/'.join(side)}改动: {first_line(src)}")
    else:
        lines.append("- （没有基准数据；请整体对比两边的 cell）")
    if r["problems"]:
        lines += ["", "结构问题："] + [f"- {p}" for p in r["problems"]]
    lines += [
        "",
        "要求：",
        "1. 逐格对齐：cell 数、cell 类型、MyST 标签必须与另一侧一致",
        "2. 代码格里只允许改注释和字符串；代码逻辑必须与另一侧逐 token 相同（check_sync 会校验）",
        "3. 中文页不得出现假名，可以保留英文（NumPy / ndarray / ufunc 等）；术语按 tools/glossary.tsv",
        "4. 改完后用 C:\\\\pixi_env 的 python 执行该 notebook，刷新输出：",
        f"   python tools/exec_notebook.py scipybook_cn/{zh_name(name)}.ipynb",
        f"5. 最后跑 `python tools/check_sync.py {zh_name(name)}` 直到没有 problems，再跑",
        f"   `python tools/check_sync.py --update-state {zh_name(name)}` 记录新的同步基准",
        "6. 报告：改了哪些 cell、执行是否成功、check_sync 的输出",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- toc
def update_toc() -> None:
    import yaml

    data = yaml.safe_load((JA_DIR / "_toc.yml").read_text(encoding="utf-8"))
    parts = []
    for part in data.get("parts", []):
        chapters = [{"file": zh_name(c["file"])} for c in part.get("chapters", [])
                    if (ZH_DIR / f"{zh_name(c['file'])}.ipynb").exists()]
        if chapters:
            entry = {"caption": part.get("caption"), "chapters": chapters}
            parts.append({k: v for k, v in entry.items() if v is not None})

    out = {"format": "jb-book", "root": data.get("root", "index")}
    if parts:
        out["parts"] = parts

    text = ("# 由 tools/check_sync.py --update-toc 生成：只列出已翻译的章节\n"
            + yaml.safe_dump(out, allow_unicode=True, sort_keys=False))
    (ZH_DIR / "_toc.yml").write_text(text, encoding="utf-8")
    print(f"written: {ZH_DIR / '_toc.yml'}")


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="只处理指定的 notebook（中文版名）")
    ap.add_argument("--prompt", action="store_true", help="输出给 AI 的同步提示")
    ap.add_argument("--update-state", action="store_true", help="记录当前状态作为同步基准")
    ap.add_argument("--update-toc", action="store_true", help="生成中文版 _toc.yml")
    ap.add_argument("--strict", action="store_true", help="有问题时返回 1")
    args = ap.parse_args()

    if args.update_toc:
        update_toc()
        return 0

    state = read_state()
    names = notebook_names(args.file)
    if not names:
        print("没有找到对应的 notebook")
        return 1

    results = [analyse(n, state) for n in names]

    if args.update_state:
        for name in names:
            jp, zp = ja_path(name), zh_path(name)
            if not (jp.exists() and zp.exists()):
                continue
            state[name] = {"ja": [cell_hash(s) for _, s in load_cells(jp)],
                           "zh": [cell_hash(s) for _, s in load_cells(zp)]}
        write_state(state)
        print(f"updated: {STATE_PATH} ({len(names)} file(s))")
        return 0

    if args.prompt:
        if len(results) != 1:
            print("--prompt 需要指定一个 notebook")
            return 1
        print(build_prompt(results[0]))
        return 0

    print_report(results)
    if args.strict:
        return 1 if any(r["problems"] for r in results) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
