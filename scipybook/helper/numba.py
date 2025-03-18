import inspect
import re
import textwrap
from IPython.display import display_markdown     

from numba.stencils import stencil

source = inspect.getsource(stencil.StencilFunc.__call__)
new_code = (re.sub(r"\.entry_point\(.+\)", "", source.replace("__call__", "_create")))
new_code = textwrap.dedent(new_code)
exec(new_code + '\nStencilFunc.create = _create\ndel _create', stencil.__dict__)

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