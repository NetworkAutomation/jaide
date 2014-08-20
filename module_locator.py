""" This is used as a workaround to getting the location of the exe file when running the windows compiled version. 
    Found at http://www.py2exe.org/index.cgi/WhereAmI
"""
import os, sys

def we_are_frozen():
    """ All of the modules are built-in to the interpreter, e.g., by py2exe
    """
    return hasattr(sys, "frozen")

def module_path():
    """ determine the location of the module/file, based on whether or not it's running as an exe.
    """
    encoding = sys.getfilesystemencoding()
    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, encoding))
    return os.path.dirname(unicode(__file__, encoding))
