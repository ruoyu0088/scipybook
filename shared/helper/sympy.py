def display_sympy_latex(expr):
    from IPython.display import display_latex
    from sympy import latex
    if isinstance(expr, tuple):
        latex_str = ", ".join(latex(item) for item in expr)
    else:
        latex_str = latex(expr)
    latex_str = "$${}$$".format(latex_str)
    display_latex(latex_str, raw=True)