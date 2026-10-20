from collections import defaultdict


def class_tree(cls):
    return { cls.__name__: [class_tree(sub_class) for sub_class in cls.__subclasses__()] }


def tree_lines(p, last=True, header=''):
    elbow = "└──"
    pipe = "│  "
    tee = "├──"
    blank = "   "
    name = list(p.keys())[0]
    lines = [header + (elbow if last else tee) + name]
    children = p[name]
    for i, c in enumerate(children):
        lines.extend(tree_lines(c, header=header + (blank if last else pipe),
                                last=i == len(children) - 1))
    return lines


def print_tree(p, last=True, header=''):
    print("\n".join(tree_lines(p, last=last, header=header)))


def print_subclasses(cls, return_str=False, as_html=False, height=300):
    """显示 cls 的继承树。

    as_html=True 时返回 IPython.display.HTML：等宽的 <pre>，超过 height 像素就纵向滚动，
    比 TextAreaInput 省地方，颜色跟随主题。return_str=True 时返回字符串。
    """
    text = "\n".join(tree_lines(class_tree(cls)))
    if as_html:
        from html import escape
        from IPython.display import HTML

        style = (f"max-height:{height}px; margin:0; overflow:auto; "
                 "white-space:pre; tab-size:4;")
        return HTML(f'<pre style="{style}">{escape(text)}</pre>')
    if return_str:
        return text + "\n"
    print(text)


def search_arguments(targets, search_name):
    import inspect
    for obj in targets:
        print("-" * 20)
        for name in dir(obj):
            val = getattr(obj, name)
            try:
                args = [p.name for p in inspect.signature(val).parameters.values()]
                null_args = [arg for arg in args if search_name in arg]
                if null_args:
                    print(f'{val.__qualname__}: {",".join(null_args)}')
            except (ValueError, TypeError):
                pass


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret
