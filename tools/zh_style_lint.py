#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Score thinking_code_cn markdown against the author's measured prose band.

Usage:
    python zh_style_lint.py --all            # every chapter, worst first
    python zh_style_lint.py z3_intro ...     # named chapters (no .ipynb needed)
    python zh_style_lint.py z3_intro --diff   # also print offending lines

Exit code 1 if any HARD metric is out of band. `ortools-sat_api` is a
reference-style chapter: only SOFT (lexical) signals matter there, so pass
--soft to downgrade HARD failures to warnings.

Reference values come from the author's published book (scipybook2 docx,
2.9e5 chars) and scipybook3 notebooks (1.8e5 chars); see
references/zh-prose-rewrite.md.
"""
import argparse
import glob
import json
import os
import re
import statistics as st
import sys

CJK = re.compile(r'[\u4e00-\u9fff]')
CN = r"C:/Users/ruoyu/Documents/notebooks/scipybook/scipybook_cn"

# (min, max) — None means one-sided
BAND = {
    # 校准自作者自己的 scipybook3（同一套 measure：1238 段 / 3003 句）
    'sent_mean': (27.0, 33.0),   # nb3 = 30.1
    'short': (0.0, 0.10),        # <=12 汉字；nb3 = 0.06
    'long': (0.10, 0.18),        # >=45 汉字；nb3 = 0.14
    'para': (55.0, None),        # 纯正文段落均长；nb3 = 73，中文书现状 35
    'q_per_10k': (0.0, 2.0),     # 问号；nb3 ≈ 0
    'ni': (0.0, 0.0),            # 你 / 您；nb3 = 0
    'fw_paren_per_10k': (0.0, 3.0),  # 数学之外的半角括号已够用
    'colloq': (0.0, 0.0),
}
# 段落均长只作参考：本书多数格是日语正本里的一两句说明格，格内段落再长就是灌水
ADVISORY = {'para'}
HARD = set(BAND)

# SOFT: lexical signals — must move toward the author's density, no hard fail
SOFT_MIN = {'由于': 10, '因此': 20, '下面': 25, '注意': 3, '例如': 8, '其': 30, '表示': 18}
SOFT_MAX = {'所以': 6, '于是': 4, '接下来': 3}

COLLOQ = ['脾气', '掏', '塞', '收工', '门道', '写岔', '搞定', '压不住', '瞅', '说白了',
          '其实就是', '炸了', '玩意儿', '活儿', '别急', '咱', '呢？', '吧。',
          # 以下均实测为作者 47 万字语料里从未出现的口语动词／生造比喻
          '摆出来', '摆出', '收上来', '第一路', '第二路', '套路', '乱撞', '冒出来',
          '钉成', '钉在', '砍掉', '顺手', '一眼', '摊开', '走过', '跑一遍', '最笨',
          '省事', '东西', '弄混', '撞到']


def md_cells(path):
    nb = json.load(open(path, encoding='utf-8'))
    return ["".join(c['source']) for c in nb['cells'] if c['cell_type'] == 'markdown']


def measure(path):
    mds = md_cells(path)
    txt = '\n'.join(mds)
    n = max(1, len(CJK.findall(txt)))
    # 纯正文段落：砍掉围栏、标题、表格、列表、引用、数学、HTML 之后剩下的行
    paras = []
    for cell in mds:
        cell = re.sub(r'```.*?```', '', cell, flags=re.S)
        cur = []
        for line in cell.split('\n'):
            t = line.strip()
            if not t or t[0] in '#|>-*!<$`' or re.match(r'^\d+\.', t):
                if cur:
                    paras.append(' '.join(cur))
                    cur = []
                continue
            cur.append(t)
        if cur:
            paras.append(' '.join(cur))
    paras = [p for p in paras if len(CJK.findall(p)) >= 15]
    sents = [s for p in paras for s in re.split(r'(?<=[。！？])', p)
             if len(CJK.findall(s)) >= 6] or ['']
    lens = [len(CJK.findall(s)) for s in sents] or [0]
    # 纯正文：去掉数学块、inline code 与非指令型围栏（正文围栏＝题目原文，算引文不算作者口气）
    plain = txt
    plain = re.sub(r'(?m)^[ \t]*`{3,}(?!\{)[^\n]*\n.*?^[ \t]*`{3,}[ \t]*$', '', plain,
                   flags=re.S)
    plain = re.sub(r'\$\$.*?\$\$', '', plain, flags=re.S)
    plain = re.sub(r'\$[^$\n]*\$', '', plain)
    plain = re.sub(r'`[^`\n]*`', '', plain)
    # 引用块（题面原文）是引文，不算作者口气：不计问号与全角括号
    plain = re.sub(r'(?m)^[ \t]*>.*$', '', plain)
    return {
        'name': os.path.basename(path)[:-6],
        'chars': n,
        'sent_mean': round(st.mean(lens), 1),
        'short': round(sum(1 for x in lens if x <= 12) / len(lens), 2),
        'long': round(sum(1 for x in lens if x >= 45) / len(lens), 2),
        'para': round(st.mean([len(CJK.findall(p)) for p in paras]), 1) if paras else 0.0,
        'q_per_10k': round(plain.count('？') / n * 10000, 1),
        'ni': plain.count('你') + plain.count('您'),
        'fw_paren_per_10k': round(plain.count('（') / n * 10000, 1),
        'colloq': sum(txt.count(w) for w in COLLOQ),
        '_txt': txt,
        '_sents': sents,
    }


def verdict(m, soft):
    fails = []
    for k, (lo, hi) in BAND.items():
        v = m[k]
        if v < lo or (hi is not None and v > hi):
            if k in ADVISORY:
                tag = 'NOTE'
            else:
                tag = 'WARN' if soft else 'FAIL'
            fails.append((tag, f'{k}={v} (band {lo}~{hi})'))
    return fails


def soft_report(m):
    n = m['chars']
    out = []
    for w, lo in SOFT_MIN.items():
        v = m['_txt'].count(w) / n * 10000
        if v < lo:
            out.append(f'{w}={v:.0f}/万字 < {lo}')
    for w, hi in SOFT_MAX.items():
        v = m['_txt'].count(w) / n * 10000
        if v > hi:
            out.append(f'{w}={v:.0f}/万字 > {hi}')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='*')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--soft', action='store_true', help='reference-style chapter')
    ap.add_argument('--diff', action='store_true', help='print offending sentences')
    a = ap.parse_args()

    if a.all or not a.names:
        paths = sorted(glob.glob(os.path.join(CN, '*.ipynb')))
    else:
        paths = [os.path.join(CN, nm if nm.endswith('.ipynb') else nm + '.ipynb') for nm in a.names]

    bad = 0
    rows = [measure(p) for p in paths if os.path.exists(p)]
    rows.sort(key=lambda r: r['sent_mean'])
    print(f"{'chapter':24s}{'字':>7s}{'句长':>6s}{'短句':>6s}{'长句':>6s}{'段长':>6s}"
          f"{'问号':>6s}{'你':>4s}{'全角(':>6s}{'口语':>5s}")
    for m in rows:
        print(f"{m['name']:24s}{m['chars']:7d}{m['sent_mean']:6.1f}{m['short']:6.2f}{m['long']:6.2f}"
              f"{m['para']:6.1f}{m['q_per_10k']:6.1f}{m['ni']:4d}{m['fw_paren_per_10k']:6.1f}{m['colloq']:5d}")
        fails = verdict(m, a.soft)
        soft = soft_report(m)
        if fails:
            print('    ' + '; '.join(f'{t} {msg}' for t, msg in fails))
            bad += sum(1 for t, _ in fails if t == 'FAIL')
        if soft:
            print('    lexical: ' + '; '.join(soft))
        if a.diff and (fails or soft):
            for s in m['_sents']:
                if (any(w in s for w in COLLOQ) or '你' in s or '您' in s
                        or '？' in s or '（' in s or len(CJK.findall(s)) <= 12):
                    print('      - ' + s.strip())
    print(f'\n{len(rows)} chapters; band: 句长 28-30, 短句 .08-.11, 长句 .13-.14, 问号 ~0, 你 0, 全角 0')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
