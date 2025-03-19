import numpy as np
from plotly import graph_objects as go


def polydata_to_lines(polydata, color="blue", scatter=None):
    x, y, z = polydata.points.T
    _, i, j = polydata.lines.reshape(-1, 3).T

    nan_arr = np.full(j.shape[0], np.nan)

    xs = np.c_[x[i], x[j], nan_arr].ravel()
    ys = np.c_[y[i], y[j], nan_arr].ravel()
    zs = np.c_[z[i], z[j], nan_arr].ravel()

    if scatter is None:
        scatter = go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", line=go.scatter3d.Line(color=color))
    else:
        scatter.x = xs
        scatter.y = ys
        scatter.z = zs
    return scatter  