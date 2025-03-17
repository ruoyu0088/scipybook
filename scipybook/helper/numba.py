import inspect
from IPython.display import display_markdown     


def get_local_variables(func, sig):
    if isinstance(sig, int):
        sig = func.signatures[sig]
    return func.overloads[sig].type_annotation.typemap

def _render_markdown(func):
    markdown_template = '```python\n# {}: {}\n{}\n```'
    source_file = inspect.getsourcefile(func)
    source = inspect.getsource(func)
    _, line = inspect.getsourcelines(func)
    markdown = markdown_template.format(source_file, line, source)
    display_markdown(markdown, raw=True)


def display_func_code(f, key):
    if key in f.targetctx._defns:
        res = f.targetctx._defns[key]
        if res._cache:
            for val in res._cache.values():
                _render_markdown(val)

    for reg in f.targetctx.typing_context._registries:
        for k, res in reg.globals:
            if k == key:
                for template in res.templates:
                    try:
                        _render_markdown(template._overload_func)
                    except Exception as ex:
                        pass    