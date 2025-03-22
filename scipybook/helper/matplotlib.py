import numpy as np
import matplotlib.pyplot as plt
from functools import wraps
import numpy as np
import matplotlib as mpl


plt.rcParams['font.family'] = "MS Gothic"

def draw_grid(ax, grid, size=6, margin=0.02, fontsize=16):
    from matplotlib import pyplot as plt
    cols = len(grid[0])
    rows = len(grid)
    aspect = rows / float(cols)
    
    line_props = dict(transform=ax.transAxes, lw=1, color="#777777")
    
    width = (1-2*margin) / cols
    height = (1-2*margin) / rows

    for i in np.linspace(margin, 1-margin, rows+1):
        line = plt.Line2D([margin, 1-margin], [i, i], **line_props)
        ax.add_artist(line)
        
    for i in np.linspace(margin, 1-margin, cols+1):
        line = plt.Line2D([i, i], [margin, 1-margin], **line_props)
        ax.add_artist(line)
        
    for (r, c), v in np.ndenumerate(grid):
        text = plt.Text(margin + c*width + width*0.5, 
                        margin + (rows-r-1)*height + height*0.5, 
                        "%s" % v, transform=ax.transAxes, 
                        va="center", ha="center", fontsize=fontsize)
        ax.add_artist(text)


def drawfunc(func):
    @wraps(func)
    def wrap(self, *arg, **kw):
        parameters = self.parameters.copy()
        parameters.update(kw)
        artist = func(self, *arg)
        for k, v in parameters.items():
            setfunc = getattr(artist, "set_{0}".format(k), None)
            if setfunc is not None:
                setfunc(v)
        artist.figure = self.renderer
        artist.set_transform(self.trans)
        artist.draw(self.renderer)
        
    return wrap
        

class ImageDrawer:
    def __init__(self, arr, reverse=True):
        from matplotlib.transforms import Affine2D, IdentityTransform
        from matplotlib.backends.backend_agg import RendererAgg

        self.arr = arr
        self.height, self.width, _ = self.arr.shape
        
        renderer = RendererAgg(self.width, self.height, 90)
        renderer.get_figure = lambda root=True:renderer
        img = mpl.image.BboxImage(renderer.bbox)
        img.set_data(arr)
        img.draw(renderer)
        
        self.renderer = renderer
        
        if not reverse:
            self.trans_offset = self.trans = IdentityTransform()
        else:
            self.trans_offset = Affine2D().scale(1, -1)
            self.trans = Affine2D().scale(1, -1).translate(0, self.height)
        self.parameters = {}
        
    def set_parameters(self, **kw):
        self.parameters = kw
            
    def to_array(self):
        buf = self.renderer.buffer_rgba()
        arr = np.frombuffer(buf, np.uint8)
        arr.shape = self.height, self.width, -1
        return arr        
        
    def save(self, fn):
        import cv2
        cv2.imwrite(fn, self.to_array()[:, :, -2::-1])
        
    @drawfunc
    def line(self, x0, y0, x1, y1):
        return mpl.lines.Line2D([x0, x1], [y0, y1])
        
    @drawfunc
    def lines(self, xs, ys):
        line = mpl.lines.Line2D(xs, ys)
        return line
        
    @drawfunc
    def circle(self, x, y, r):
        circle = mpl.patches.Circle((x, y), r)
        return circle
        
    @drawfunc
    def rectangle(self, x, y, w, h):
        rect = mpl.patches.Rectangle((x, y), w, h)
        return rect
        
    @drawfunc
    def ellipse(self, x, y, w, h, angle=0):
        ellipse = mpl.patches.Ellipse((x, y), w, h, angle=angle)
        return ellipse
        
    @drawfunc
    def text(self, x, y, text):
        text = mpl.text.Text(x, y, text)
        return text
        
    @drawfunc
    def markers(self, mark, x, y, size):
        marker = mpl.markers.MarkerStyle(mark)
        
        path = marker.get_path()
        collection = mpl.collections.PathCollection(
                (path,), size,
                offsets = list(zip(x, y)),
                transOffset = self.trans_offset
                )
        return collection
                                                