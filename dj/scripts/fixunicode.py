"""
Module which forces stdout/stderr into a mode which allows unicode output.
"""
import sys

try:
    sys.stdout.write(u"\u2603")
    sys.stdout.write(u"\b")
except UnicodeEncodeError, e:
    pass

try:
    sys.stderr.write(u"\u2603")
    sys.stderr.write(u"\b")
except UnicodeEncodeError, e:
    pass

if sys.stdout.encoding != "UTF-8" or sys.stderr.encoding != "UTF-8":

    from ctypes import pythonapi, py_object, c_char_p
    PyFile_SetEncoding = pythonapi.PyFile_SetEncoding
    PyFile_SetEncoding.argtypes = (py_object, c_char_p)

    if sys.stdout.encoding != "UTF-8":
        if not PyFile_SetEncoding(sys.stdout, "UTF-8"):
            raise SystemError("Unable to force stdout to UTF-8, PyFile_SetEncoding failed.")
        
        if sys.stdout.encoding != "UTF-8":
            raise SystemError("Unable to force stdout to UTF-8, encoding still %s." % sys.stdout.encoding)

    
    if sys.stderr.encoding != "UTF-8":
        if not PyFile_SetEncoding(sys.stderr, "UTF-8"):
            raise SystemError("Unable to force stderr to UTF-8, PyFile_SetEncoding failed.")
        
        if sys.stderr.encoding != "UTF-8":
            raise SystemError("Unable to force stderr to UTF-8, encoding still %s." % sys.stderr.encoding)

try:
    sys.stdout.write(u"\u2603")
    sys.stdout.write(u"\b")
except UnicodeEncodeError, e:
    raise SystemError("Unable to write unicode on stdout (encoding %s).\n%s" % (sys.stdout.encoding, e))

try:
    sys.stderr.write(u"\u2603")
    sys.stderr.write(u"\b")
except UnicodeEncodeError, e:
    raise SystemError("Unable to write unicode on stderr (encoding %s).\n%s" % (sys.stderr.encoding, e))
