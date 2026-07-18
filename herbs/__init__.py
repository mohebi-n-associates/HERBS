"""
``HERBS Code``
================

Functions present in herbs are listed below.


For Image Processing
--------------------------

   ...
   ...

For Atlas
--------------

   ...

For Others
------------------

   ...


"""

from .run_herbs import run_herbs

__all__ = ["run_herbs", "CZIReader"]


def __getattr__(name):
    if name == "CZIReader":
        from .czi_reader import CZIReader

        return CZIReader
    raise AttributeError("module {!r} has no attribute {!r}".format(__name__, name))
