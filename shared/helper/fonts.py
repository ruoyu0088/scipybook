"""matplotlib で日本語・中国語を表示するためのフォント設定。

この本の図には日本語(将来は中国語)のラベルが入るので、matplotlib の既定の
DejaVu Sans では豆腐(□)になる。ここで言語に合ったフォントを選び、rcParams に
設定する。呼び出しは helper.matplotlib の import 時に 1 回だけ行う。

使い方:
    import helper.matplotlib        # これだけで日本語フォントが設定される
    from helper.fonts import setup
    setup("zh")                     # 中国語に切り替える

言語の決め方(優先順):
    1. 引数 lang
    2. 環境変数 SCIPYBOOK_LANG ("ja" / "zh")
    3. カレントディレクトリが scipybook_cn なら "zh"、それ以外は "ja"
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager as fm

# 言語ごとの候補。前にあるものほど優先する。MS Gothic(とその仲間)は
# 下の BROKEN で外すので、ここには入れない。
CANDIDATES = {
    "ja": [
        "Yu Gothic",
        "Meiryo",
        "Noto Sans JP",
        "Noto Sans CJK JP",
        "IPAPGothic",
        "BIZ UDPGothic",
    ],
    "zh": [
        "Microsoft YaHei",
        "Noto Sans SC",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "SimHei",
        "PingFang SC",
        "WenQuanYi Zen Hei",
    ],
}

# この環境の msgothic.ttc は、matplotlib 3.11 の Agg で文字がまったく描かれない
# (エラーも警告も出ず、テキストだけ消える)。候補から外す。
BROKEN = {"MS Gothic", "MS PGothic", "MS UI Gothic", "MS PMincho", "MS Mincho"}

PROBE = {"ja": "日本語の表示", "zh": "中文显示"}

_lang = None
_family = None


def _bundled_font_dirs() -> list[Path]:
    """helper/fonts/ に置いたフォントを matplotlib に登録する。"""
    root = Path(__file__).resolve().parent / "fonts"
    if not root.is_dir():
        return []
    added = []
    for path in sorted(root.iterdir()):
        if path.suffix.lower() in {".ttf", ".otf", ".ttc"}:
            try:
                fm.fontManager.addfont(str(path))
                added.append(path)
            except Exception:  # 壊れたフォントは無視する
                pass
    return added


def _renders(family: str, text: str) -> bool:
    """そのフォントで実際に文字が描けるかを、小さな図を描いて確かめる。"""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    try:
        fig = Figure(figsize=(1.2, 0.4), dpi=50)
        FigureCanvasAgg(fig)
        fig.text(0.05, 0.3, text, family=family, fontsize=10)
        fig.canvas.draw()
        buf = fig.canvas.buffer_rgba()
    except Exception:
        return False
    # 背景(白)以外の画素が 1 つでもあれば、文字が描けている
    import numpy as np

    px = np.frombuffer(buf, dtype=np.uint8).reshape(-1, 4)[:, :3]
    return bool((px < 250).any())


def pick(lang: str | None = None) -> str:
    """使えるフォント名を 1 つ返す。どれも使えなければ DejaVu Sans。"""
    global _lang, _family
    if lang is None:
        lang = os.environ.get("SCIPYBOOK_LANG")
    if lang is None:
        cwd = Path.cwd()
        lang = "zh" if cwd.name.endswith("_cn") or "scipybook_cn" in str(cwd) else "ja"
    if _family and lang == _lang:
        return _family

    _bundled_font_dirs()
    installed = {f.name for f in fm.fontManager.ttflist}
    text = PROBE.get(lang, PROBE["ja"])
    for family in CANDIDATES.get(lang, CANDIDATES["ja"]):
        if family not in installed or family in BROKEN:
            continue
        if _renders(family, text):
            _lang, _family = lang, family
            return family
    _lang, _family = lang, "DejaVu Sans"
    import warnings

    warnings.warn(
        f"{text!r} を描ける CJK フォントが見つかりません。図の日本語/中国語が豆腐になります。",
        RuntimeWarning,
        stacklevel=2,
    )
    return _family


def setup(lang: str | None = None) -> str:
    """rcParams にフォントを設定する。戻り値は選んだフォント名。"""
    family = pick(lang)
    mpl.rcParams["font.family"] = "sans-serif"
    # 先頭が本文用。あとは字形が欠けたときの保険。
    rest = [f for f in CANDIDATES.get(_lang or "ja", []) if f != family and f not in BROKEN]
    mpl.rcParams["font.sans-serif"] = [family, *rest, "DejaVu Sans"]
    # CJK フォントに U+2212(真のマイナス)が無いと目盛りが化ける
    mpl.rcParams["axes.unicode_minus"] = False
    return family


def current() -> str:
    return _family or pick()
