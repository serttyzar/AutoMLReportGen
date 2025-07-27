__all__ = ["load_ipython_extension"]

from importlib import import_module
from IPython import get_ipython

def load_ipython_extension(ipython):
    """IPython hook: %load_ext autoreport"""
    magics = import_module("autoreport.magics")
    ipython.register_magics(magics.AutoReportMagics)

_IP = get_ipython()
if _IP:             
    load_ipython_extension(_IP)