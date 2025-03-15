import html
import pyvista as pv


def iframe(html_text, height="500px", width="500px"):
    html_code = html.escape(html_text)
    iframe = f'<iframe srcdoc="{html_code}" height="{height}" width="{width}" sandbox="allow-scripts allow-same-origin" scrolling="no"></iframe>'
    return iframe

def plotter_to_iframe(plotter, width=500, height=500, return_html=False):
    from IPython.display import display_html
    
    if isinstance(width, int):
        width = f"{width}px"
    
    if isinstance(height, int):
        height = f"{height}px"

    html = plotter.export_html(None).getvalue()
    iframe_str = iframe(html, height=f"{height}px", width=f"{width}px")
    if return_html:
        return iframe_str
    else:
        display_html(iframe_str, raw=True)
