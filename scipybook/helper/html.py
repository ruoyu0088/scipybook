def html_table(rows, columns_name, title=None):
    from tabulate import tabulate
    from IPython.display import display_html, HTML
    table = tabulate(rows, columns_name, "html")

    if title is not None:
        table = f'{title}\n\n{table}'

    display_html(HTML(table))