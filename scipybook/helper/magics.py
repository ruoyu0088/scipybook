from IPython.core.magic import register_line_magic, register_cell_magic, register_line_cell_magic
from IPython.core.interactiveshell import InteractiveShell
from IPython.lib.pretty import pretty as _pretty


def pretty(obj):
    import numpy as np
    if isinstance(obj, np.ndarray):
        return np.array2string(obj, separator=", ")
    else:
        return _pretty(obj)


@register_line_magic
def C(line):
    from itertools import zip_longest
    sh = InteractiveShell.instance()
    pos = line.find(" ")
    try:
        gap = int(line[:pos])
        line = line[pos+1:]
    except ValueError:
        gap = 2

    for idx, sec in enumerate(line.split(";;")):
        if idx > 0:
            print()
        codes = [x.strip() for x in sec.split(";")]
        results = [[code] for code in codes]
        for i, code in enumerate(codes):
            results[i].extend(pretty(sh.ev(code)).split("\n"))

        results = [list(row) for row in zip(*list(zip_longest(*results, fillvalue="")))]

        for i, col in enumerate(results):
            width = max(len(row) for row in col)
            col.insert(1, "-"*width)
            col[0] = col[0].center(width)
            col[2:] = [row.ljust(width) for row in col[2:]]

        for row in zip(*results):
            print((" "*gap).join(row))


@register_line_magic
def col(line):
    sh = InteractiveShell.instance()
    pos = line.find(" ")
    n = int(line[:pos])
    code = line[pos+1:]
    result = pretty(sh.ev(code)).split("\n")
    max_width = max(len(line) for line in result) + 3
    result = [line.ljust(max_width) for line in result]
    result = "\n".join(["".join(result[i:i+n])
        for i in range(0, len(result), n)])
    print(result)


@register_line_magic
def omit(line):
    sh = InteractiveShell.instance()
    import sys
    pos = line.find(" ")
    try:
        count = int(line[:pos])
        line = line[pos+1:]
    except ValueError:
        count = 4

    lines = []
    def write(s):
        lines.append(s)

    def flush():
        pass

    write.flush = flush

    write.write = write
    try:
        old_stdout = sys.stdout
        sys.stdout = write
        result = sh.ev(line)
    finally:
        sys.stdout = old_stdout

    if lines:
        stdout = "".join(lines).split("\n")[:count]
        indent = len(stdout[-1]) - len(stdout[-1].lstrip())
        stdout.append(" "*indent + "...")
        stdout_lines = "\n".join(stdout)
        sys.stdout.write(stdout_lines)
    if result:
        print("\n".join(sh.display_formatter.formatters["text/plain"](result).split("\n")[:count]))
        print("...")    


@register_line_magic
def latex(line):
    from .sympy import display_sympy_latex
    from IPython.core.interactiveshell import InteractiveShell
    sh = InteractiveShell.instance()
    expr = sh.ev(line)
    display_sympy_latex(expr)            