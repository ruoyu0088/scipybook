from distutils.command.build import build
from distutils.command.build_ext import build_ext
from Cython.Build.IpythonMagic import CythonMagics


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