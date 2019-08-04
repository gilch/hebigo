import sys
sys.path.append('./src')
import hebi.parser

hebi.parser.transpile(hebi, "basic")
hebi.parser.transpile(__package__, "native_tests")
