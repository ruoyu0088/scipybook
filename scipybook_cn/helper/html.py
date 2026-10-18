import html

def iframe(html_text, height="500px", width="500px"):
    html_code = html.escape(html_text)
    iframe = f'    <iframe srcdoc="{html_code}" height="{height}" width="{width}" sandbox="allow-scripts allow-same-origin" scrolling="no"></iframe>    '
    return iframe

def html_table(rows, columns_name, title=None):
    from tabulate import tabulate
    from IPython.display import display_html, HTML
    table = tabulate(rows, columns_name, "html")

    if title is not None:
        table = f'{title}\n\n{table}'

    display_html(HTML(table))


def latex_table(rows, columns_names, latex_columns):
    import polars as pl
    from great_tables import GT
    df = pl.DataFrame(rows, schema=columns_names, orient="row")

    def as_math(text):
        return rf'<div class="math">\[{text}\]</div>'
        
    return GT(df).fmt(columns=latex_columns, fns=as_math)