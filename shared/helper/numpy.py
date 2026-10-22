import numpy as np


def array_pretty(obj):
    print(f'{obj.dtype.name} shape:{obj.shape} strides:{obj.strides} ', end='')
    flags = ['writeable', 'c_contiguous', 'f_contiguous', 'owndata']
    flags = [flag[0].upper() for flag in flags if getattr(obj.flags, flag)]
    print('|'.join(flags)) 
    print(np.array2string(obj, suppress_small=True, precision=4))    

def concat_images(images, margin=10):
    import numpy as np
    width = sum(img.shape[1] for img in images) + (len(images)-1)*margin
    height = max(img.shape[0] for img in images)
    image = np.empty((height, width, 3), dtype=np.uint8)
    image.fill(255)
    x = 0
    
    for img in images:
        if img.dtype in (np.float32, np.float64):
            img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
        h, w = img.shape[:2]
        if img.ndim == 2:
            img = img[:, :, None]
        elif img.ndim == 3:
            img = img[:, :, :3]
        image[:h, x:x+w, :] = img[:, :, :]
        x += w + margin

    return image

def display_image(image):
    import io
    from matplotlib.image import imsave
    from IPython import display
    buf = io.BytesIO()
    imsave(buf, image)
    return display.display_png(display.Image(buf.getvalue()))

def array_image(*images):
    return display_image(concat_images(images))