"""DLL wrapper"""
import os
import sys
import warnings

from ctypes import CDLL
from ctypes.util import find_library


# Prints warning without stack or line info
def prettywarn(msg, warntype):
    original = warnings.showwarning

    def _warning(message, category, filename, lineno, file=None, line=None):
        print(message)

    warnings.showwarning = _warning
    warnings.warn(msg, warntype)
    warnings.showwarning = original


__all__ = ["DLL", "nullfunc"]


def _findlib(libnames, path=None):
    """Finds libraries and returns them in a list, with libraries found in the directory
    optionally specified by 'path' being first (taking precedence) and libraries found in system
    search paths following.
    """

    platform = sys.platform
    if platform == "win32":
        patterns = ["{0}.dll"]
    elif platform == "darwin":
        patterns = ["lib{0}.dylib", "{0}.framework/{0}", "{0}.framework/Versions/A/{0}"]
    else:
        patterns = ["lib{0}.so"]

    searchfor = libnames
    results = []
    if path and path.lower() != "system":
        # First, find any libraries matching pattern exactly within given path
        for libname in searchfor:
            for subpath in str.split(path, os.pathsep):
                for pattern in patterns:
                    dllfile = os.path.join(subpath, pattern.format(libname))
                    if os.path.exists(dllfile):
                        results.append(dllfile)

        # Next, on Linux and similar, find any libraries with version suffixes matching pattern
        # (e.g. libSDL2.so.2) at path and add them in descending version order (i.e. newest first)
        if platform not in ("win32", "darwin"):
            versioned = []
            files = os.listdir(path)
            for f in files:
                for libname in searchfor:
                    dllname = "lib{0}.so".format(libname)
                    if dllname in f and not (dllname == f or f.startswith(".")):
                        versioned.append(os.path.join(path, f))
            versioned.sort(key=_so_version_num, reverse=True)
            results = results + versioned

    # Finally, search for library in system library search paths
    for libname in searchfor:
        dllfile = find_library(libname)
        if dllfile:
            # For Python 3.8+ on Windows, need to specify relative or full path
            if os.name == "nt" and not ("/" in dllfile or "\\" in dllfile):
                dllfile = "./" + dllfile
            results.append(dllfile)

    return results


class DLLWarning(Warning):
    pass


def lazy_function_error(exception):
    def raise_error(*args, **kwargs):
        raise exception
    return raise_error


class DLL(object):
    """Function wrapper around the different DLL functions. Do not use or
    instantiate this one directly from your user code.
    """

    def __init__(self, libinfo, libnames, path=None, env_override=None):
        self._dll = None
        self._libname = libinfo

        foundlibs = _findlib(libnames, path)

        dllmsg = ''
        if env_override:
            dllmsg = f"({env_override}: {os.getenv(env_override) or 'unset'})" % ()

        if len(foundlibs) == 0:
            raise RuntimeError(f'could not find any library for {libinfo} ({dllmsg})')

        for libfile in foundlibs:
            try:
                self._dll = CDLL(libfile)
                self._libfile = libfile
                break

            except Exception as exc:
                # Could not load the DLL, move to the next, but inform the user
                # about something weird going on - this may become noisy, but
                # is better than confusing the users with the RuntimeError below
                warnings.warn(repr(exc), DLLWarning)

        if self._dll is None:
            raise RuntimeError(f"found {foundlibs}, but it's not usable for the library {libinfo}")

        if path is not None and sys.platform in ("win32",) and path in self._libfile:
            os.environ["PATH"] = "%s;%s" % (path, os.environ["PATH"])

    def bind_function(self, funcname, args=None, returns=None, **kwargs):
        """Binds the passed argument and return value types to the specified
        function. If the version of the loaded library is older than the
        version where the function was added, an informative exception will
        be raised if the bound function is called.

        Args:
            funcname (str): The name of the function to bind.
            args (List or None, optional): The data types of the C function's
                arguments. Should be 'None' if function takes no arguments.
            returns (optional): The return type of the bound C function. Should
                be 'None' if function returns 'void'.
            added (str, optional): The version of the library in which the
                function was added, in the format '2.x.x'.

            kwargs (dict): used to hold arbitrary data from the c-binding generator
        """
        func = getattr(self._dll, funcname, None)

        if not func:
            v = ValueError(f"Could not find function '{funcname}' in {self._libfile}")
            warnings.warn(str(v))
            return lazy_function_error(v)

        func.argtypes = args
        func.restype = returns
        return func

    @property
    def libfile(self):
        """str: The filename of the loaded library."""
        return self._libfile


def _unavailable(err):
    """A wrapper that raises a RuntimeError if a function is not supported."""

    def wrapper(*fargs, **kw):
        raise RuntimeError(err)

    return wrapper


def _nonexistent(funcname, func):
    """A simple wrapper to mark functions and methods as nonexistent."""

    def wrapper(*fargs, **kw):
        warnings.warn("%s does not exist" % funcname,
                      category=RuntimeWarning, stacklevel=2)
        return func(*fargs, **kw)

    wrapper.__name__ = func.__name__
    return wrapper


def _so_version_num(libname):
    """Extracts the version number from an .so filename as a list of ints."""
    return list(map(int, libname.split('.so.')[1].split('.')))


def nullfunc(*args):
    """A simple no-op function to be used as dll replacement."""
    return


def load_sdl2():
    # Use DLLs from pysdl2-dll, if installed and DLL path not explicitly set
    try:
        prepath = os.getenv('PYSDL2_DLL_PATH')
        import sdl2dll

        postpath = os.getenv('PYSDL2_DLL_PATH')
        if prepath != postpath:
            msg = "UserWarning: Using SDL2 binaries from pysdl2-dll {0}"
            prettywarn(msg.format(sdl2dll.__version__), UserWarning)
    except ImportError:
        pass

    dll = DLL("SDL2", ["SDL2", "SDL2-2.0"], os.getenv("PYSDL2_DLL_PATH"))
    return dll.bind_function
