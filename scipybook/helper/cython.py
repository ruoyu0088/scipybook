import re
from bs4 import BeautifulSoup
from distutils.command.build import build
from distutils.command.build_ext import build_ext
from Cython.Build.IpythonMagic import CythonMagics

def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    styles = soup.head.find_all("style") if soup.head else []
    body_content = soup.body.encode_contents() if soup.body else b""
    cleaned_html = "".join(str(style) for style in styles) + body_content.decode()
    return cleaned_html

def clean_annotated_html(html):
    r = re.compile('<p>Raw output: <a href="(.*)">(.*)</a>')
    html = '\n'.join(l for l in html.splitlines() if not r.match(l))
    html = clean_html(html)
    html = html.replace("body.cython", "div.cython")
    html = html.replace("pre {", "div.pre {")
    # print(html)
    return html
    
CythonMagics.clean_annotated_html = staticmethod(clean_annotated_html)

if not hasattr(CythonMagics, '_get_build_extension_original'):
    CythonMagics._get_build_extension_original = CythonMagics._get_build_extension

    def _get_build_extension_fix(self, *args, **kwargs):
        build_extension = self._get_build_extension_original(*args, **kwargs)
        build_extension.compiler = 'mingw32'
        # defines = ('MS_WIN64', 1)
        # if build_extension.define is not None:
        #     build_extension.define.append(defines)
        # else:
        #     build_extension.define = [defines]
        return build_extension

    CythonMagics._get_build_extension = _get_build_extension_fix


def load_ipython_extension(ip):
    ip.register_magics(CythonMagics)