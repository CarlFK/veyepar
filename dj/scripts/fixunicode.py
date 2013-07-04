import sys
print sys.stdout.encoding
 
from ctypes import pythonapi, py_object, c_char_p
PyFile_SetEncoding = pythonapi.PyFile_SetEncoding
PyFile_SetEncoding.argtypes = (py_object, c_char_p)
if not PyFile_SetEncoding(sys.stdout, "UTF-8"):
         raise ValueError
