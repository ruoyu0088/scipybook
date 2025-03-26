from IPython.lib.lexers import IPython3Lexer
from pygments.lexer import bygroups, using
from pygments.token import Text, Operator
from pygments.lexers import CythonLexer, CLexer, JavascriptLexer


def setup(app):
    cython_token = (r'(?s)(\s*)(%%cython)([^\n]*\n)(.*)', bygroups(Text, Operator, Text, using(CythonLexer)))
    writefile_c_token = (r'(?s)(\s*)(%%writefile)([^\n]*\.[ch]\s*\n)(.*)', bygroups(Text, Operator, Text, using(CLexer)))
    writefile_cython_token = (r'(?s)(\s*)(%%writefile)([^\n]*\.pyx\s*\n)(.*)', bygroups(Text, Operator, Text, using(CythonLexer)))
    writefile_js_token = (r'(?s)(\s*)(%%writefile)([^\n]*\.js\s*\n)(.*)', bygroups(Text, Operator, Text, using(JavascriptLexer)))
    cffi_token = (r'(?s)(\s*)(%%cffi)([^\n]*\n)(.*)', bygroups(Text, Operator, Text, using(CLexer)))

    IPython3Lexer.tokens['root'][:0] = [cython_token, writefile_c_token, writefile_cython_token, writefile_js_token, cffi_token]

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
