import zlib
import base64
import zipfile
import io
from pathlib import Path
from IPython.display import display_html, HTML
import pyvista as pv
from .html import iframe


def export_to_small_html(plotter):
    zip_data = plotter.export_vtksz(filename=None)
    zf = zipfile.ZipFile(io.BytesIO(zip_data))
    with zf.open('index.json') as f:
        json_data = f.read()
        compressed = zlib.compress(json_data)
        b64_str = base64.b64encode(compressed).decode()

    templete_file = Path(__file__).parent / 'vtk_scene.html'
    with open(templete_file, encoding='utf-8') as f:
        html = f.read().replace("%json_data%", b64_str)

    return html


def plotter_to_iframe(plotter, width=500, height=500, return_html=False):
    
    if isinstance(width, int):
        width = f"{width}px"
    
    if isinstance(height, int):
        height = f"{height}px"

    html = export_to_small_html(plotter)

    iframe_str = iframe(html, height=f"{height}px", width=f"{width}px")
    if return_html:
        return " " * 100 + iframe_str # disable iframe warning
    else:
        # display_html(iframe_str, raw=True)
        return HTML(iframe_str)


def plot_point_indices(plotter, ds, scale, color='orange', index_name='vtkOriginalPointIds'):
    for point, normal, i in zip(ds.points, ds.point_normals, ds.point_data[index_name]):
        x, y, z = point
        nx, ny, nz = normal * scale

        text = str(int(i))
        text_3d = pv.Text3D(text, width=scale*0.5 * len(text), depth=scale*0.2, height=scale, center=(x + nx, y + ny, z + nz))
        plotter.add_mesh(text_3d, color=color)        