# read version from installed package
__all__ = ['pySurf','dataIO','pyProfile','thermal']

from importlib.metadata import version
__version__ = version("pyXsurf")