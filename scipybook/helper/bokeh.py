from collections import deque
from bokeh.core.has_props import HasProps


def find_path(root, target, root_name="", all=False, depth=16):
    todo = deque([(root, [])])
    visited = set()
    pathes = []
    
    def visit(obj, node):
        if id(obj) not in visited and len(path) < depth:
            todo.append((obj, path + [node]))
            #visited.add(id(obj))

    while todo:
        obj, path = todo.popleft()
        if obj is target:
            links = [root_name]
            for kind, link in path:
                if kind == "index":
                    links.append("[{}]".format(repr(link)))
                elif kind == "prop":
                    links.append(".{}".format(link))
            path_found = "".join(links)
            if not all:
                return path_found
            else:
                pathes.append(path_found)
        elif isinstance(obj, (tuple, list)):
            for i, obj2 in enumerate(obj):
                visit(obj2, ("index", i))
        elif isinstance(obj, dict):
            for key, obj2 in obj.items():
                visit(obj2, ("index", key))
        elif isinstance(obj, HasProps):
            for key, obj2 in obj.properties_with_values().items():
                visit(obj2, ("prop", key))
                
    return pathes 

    
def iter_all_subclasses(base):
    for class_ in base.__subclasses__():
        yield class_
        yield from iter_all_subclasses(class_)  


def widgets_demo():
    from bokeh.io import show
    from bokeh.models.widgets import Button, MultiSelect
    from bokeh.models import CustomJS, PreText
    from bokeh.layouts import column, row
    from bokeh.models.widgets import Widget
    import keyword
    from datetime import datetime

    widget_classes = []        

    for class_ in iter_all_subclasses(Widget):
        if 'abstract base' not in class_.__doc__:
            widget_classes.append(class_)

    classnames = [class_.__name__ for class_ in widget_classes if class_.__name__ not in ('DataTable', 'DataCube')]

    options = ['Item 1', 'Item 2', 'Item 3']

    arguments = dict(
        Button=dict(label='Click Me'),
        Toggle=dict(label='Toggle Me'),
        Dropdown=dict(menu=options),
        CheckboxButtonGroup=dict(labels=options),
        RadioButtonGroup=dict(labels=options),
        CheckboxGroup=dict(labels=options),
        RadioGroup=dict(labels=options),
        NumericInput=dict(title='Input a Number', value=4),
        Spinner=dict(title='Input a Number', value=10, step=0.5),
        TextInput=dict(title='Input a String', value='hello'),
        TextAreaInput=dict(title='Input a String', rows=5),
        PasswordInput=dict(title='Input a Password'),
        AutocompleteInput=dict(completions=keyword.kwlist, title='Input a Python Keyword'),
        Select=dict(options=options),
        MultiSelect=dict(options=options),
        MultiChoice=dict(options=options),
        DatePicker=dict(title='Select a Date', value=datetime.now()),
        ColorPicker=dict(title='Select a Color'),
        FileInput=dict(title='Select a File'),
        Paragraph=dict(text='This is a Paragraph'),
        PreText=dict(text='print("hello world!")'),
        Div=dict(text='This is a Div'),
        Slider=dict(start=0, end=10, step=0.1, value=5, title='Speed'),
        RangeSlider=dict(start=0, end=10, step=0.1, value=(1, 4), title='Select a Range'),
        DateSlider=dict(start=datetime(2020, 4, 1), end=datetime(2020, 5, 1), value=datetime(2020, 4, 10), 
                        title='Select a Date', format='%Y/%m/%d'),
        DateRangeSlider=dict(start=datetime(2020, 4, 1), end=datetime(2020, 5, 1), value=[datetime(2020, 4, 10), datetime(2020, 4, 14)], 
                        title='Select a Date Range', format='%Y/%m/%d'),
    )

    select = MultiSelect(options=classnames, tags=[arguments], value=[classnames[0]], size=len(classnames))
    create_button = Button(label='Create', width=100)
    arg_info = PreText()

    callback = CustomJS(code='''
    window.layout = layout;
    let args = select.tags[0];
    let classname = select.value[0];
    let class_ = Bokeh.Models.get(classname);
    let instance = new class_();
    if(classname in args){
        let arg = args[classname];
        for(let name in arg){
            instance[name] = arg[name];
        }
        arg_info.text = JSON.stringify(arg, null, 4);
    }

    layout.children = [layout.children[0], instance];
    ''')

    layout_widget = column(arg_info, height=500)
    layout = row(column(select, create_button), layout_widget)
    create_button.js_on_click(callback)
    callback.args = dict(select=select, layout=layout_widget, arg_info=arg_info)
    show(layout)


def get_glyph_properties(class_):
    for name in sorted(class_.properties()):
        if name not in ('js_event_callbacks', 'js_property_callbacks', 'name', 'tags', 'subscribed_events'):
            yield name, getattr(class_, name)  

def show_glyph_info(class_, detail_level=2):
    import textwrap
    import black
    
    for name, prop in get_glyph_properties(class_):
        bars = '-' * (len(name) + 1)
        type_text = black.format_str(str(prop.property), mode=black.FileMode())
        type_name = prop.property.__class__.__name__
        if detail_level == 1:
            print(f'{name}: {type_name}')
        elif detail_level == 2:
            print(f'{name}: \n{bars}\n{type_text}')
        elif detail_level == 3:
            doc = prop.__doc__
            if doc is None:
                doc = '...'
            doc = textwrap.indent(doc.strip(), ' '*4)
            print(f'{name}: \n{bars}\n{type_text}\n\n{doc}\n')  


def make_contours_data(X, Y, Z, levels=8):
    import numpy as np
    from skimage import measure
    
    if isinstance(levels, int):
        levels = np.linspace(Z.min(), Z.max(), levels+2)[1:-1]

    def concatenate_contours(contours):
        nan_row = np.array([[np.nan, np.nan]])
        arrays = []
        for c in contours:
            arrays.append(c)
            arrays.append(nan_row)

        return np.concatenate(arrays[:-1], axis=0)

    contours = [concatenate_contours(measure.find_contours(Z, level)) for level in levels]

    y_ptp = Y.ptp()
    y_min = Y.min()
    x_ptp = X.ptp()
    x_min = X.min()
    h, w = Z.shape
    ys = [c[:, 0] / h * y_ptp + y_min for c in contours]
    xs = [c[:, 1] / w * x_ptp + x_min for c in contours]
    return dict(xs=xs, ys=ys, levels=levels)


def encode_image_cv(image, format="RGBA"):
    import cv2
    import base64
    
    if format != 'BGRA':
        cvt_type = getattr(cv2, f'COLOR_{format}2BGRA')
        image = cv2.cvtColor(image, cvt_type)
        
    _, imgdata = cv2.imencode(".jpg", image, (cv2.IMWRITE_JPEG_QUALITY, 80))
    imgdata = imgdata.ravel()
    url = "data:image/jpeg;base64," + base64.encodebytes(imgdata).decode()
    return url

def encode_image_pil(image):
    import imageio
    import base64
    import io
    buf = io.BytesIO()
    if image.ndim == 3:
        image = image[:, :, :3]

    imageio.imwrite(buf, image, format="jpg", quality=80)
    imgdata = buf.getvalue()
    url = "data:image/jpeg;base64," + base64.encodebytes(imgdata).decode()
    return url    

def encode_image(image):
    try:
        return encode_image_pil(image)
    except:
        return encode_image_cv(image)      