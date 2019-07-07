#
# This example demonstrates usage of the Indenter class.
#
# Since indentation is context-sensitive, a postlex stage is introduced to
# manufacture INDENT/DEDENT tokens.
#
# It is crucial for the indenter that the NL_type matches
# the spaces (and tabs) after the newline.
#

from lark import Lark
from lark.indenter import Indenter

tree_grammar = r"""
    ?start: top*
    
    
    top: expr* [NAME _POLYARY (atom|unary)* (ray|NL) block?]
       
    expr: atom | unary
    atom: NAME
    unary: NAME _UNARY expr
    ray: NAME _POLYARY (atom|unary)* (ray|NL)
    
    block: INDENT (WS top NL)+ DEDENT
    
    %import common.CNAME -> NAME
    %declare INDENT DEDENT
    
    %ignore WS
    
    _UNARY: /:(?![ \n\r])/
    _POLYARY: /:(?=[ \n\r])/
    NL: /(\r?\n)+/
    //WS: /(?<!\n) +/
    WS: " "+
"""


class TreeIndenter(Indenter):
    NL_type = '_NL'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = 'INDENT'
    DEDENT_type = 'DEDENT'
    tab_len = 8


parser = Lark(
    tree_grammar,
    lexer="standard",
    parser='earley',
    postlex=TreeIndenter(),
    debug=True,
)

test_tree = """\
spam:eggs:bacon a b q:c: d e f:
"""
"""(spam (eggs bacon)) a b (q (c d e (f) x))"""
"""
a
a:b
a:b:c
a: a
"""
"""
a:b b: c: d: e
    b: q
    c:
        d
        e
    f:
        g
"""


def test():
    print(parser.parse(test_tree).pretty())


if __name__ == '__main__':
    test()

