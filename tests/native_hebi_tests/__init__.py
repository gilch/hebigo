print(__package__)

from hebi.parser import transpile

def recompile():
    transpile(__package__, "test_native")
