"""Test import the library and print essential information"""

import platform
import sys

import pshell

print("Python interpreter:", sys.executable)
print("Python version    :", sys.version)
print("Platform          :", platform.platform())
print("Library path      :", pshell.__file__)
print("Library version   :", pshell.__version__)
