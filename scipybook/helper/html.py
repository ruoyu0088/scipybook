import html

def iframe(html_text, height="500px", width="500px"):
    html_code = html.escape(html_text)
    iframe = f'<iframe srcdoc="{html_code}" height="{height}" width="{width}" sandbox="allow-scripts allow-same-origin" scrolling="no"></iframe>'
    return iframe

def html_table(rows, columns_name, title=None):
    from tabulate import tabulate
    from IPython.display import display_html, HTML
    table = tabulate(rows, columns_name, "html")

    if title is not None:
        table = f'{title}\n\n{table}'

    display_html(HTML(table))