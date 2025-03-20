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