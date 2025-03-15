import numpy as np
import matplotlib.pyplot as plt

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