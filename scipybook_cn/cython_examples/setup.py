from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

vector = Extension("vector", ["vector.pyx"])

multisearch = Extension("multisearch",
                        ["multisearch.pyx", "ahocorasick/ahocorasick.c",
                         "ahocorasick/node.c"],
                        include_dirs=["ahocorasick"])

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [vector, multisearch]
)