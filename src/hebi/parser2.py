import ast
import re

TOKEN = re.compile(r"""(?x)
 (?P<empty>\([ \r\n]*\))
|(?P<python>[([{]|(?:[rR][bfBF]?|[bfBF][rR]?|[uU])?(?:['"]|'''|["]""))
|(?P<end>[)\]{]|["]""|'''|['"])
|(?P<comment>\n?[ ]*[#].*)
|(?P<indent>(?<=\n)[ ]*(?=[^\r\n]))
|(?P<blank>\r?\n)
|(?P<sp>[ ])
|(?P<eol>(?<=\n))
|(?P<unary>(?:\w+|:):(?=[^ \r\n]))
|(?P<polyadic>(?:\w+|:):(?=[ \r\n]))
|(?P<key>:\w*)
|(?P<symbol>[^ \r\n])
|(?P<error>.)
""")

def end(s):
    for q in ['"""', "'''", "'", '"']:
        if q in s:
            return q
    return {'(':')','[':']','{':'}'}[s]

IGNORE = frozenset({
    'comment',
    'sp',
    'blank',
})
def lex(code):
    opens = 0
    indents = [0]
    tokens = iter(TOKEN.finditer(code+'\n'))
    for token in tokens:
        case = token.lastgroup
        group = token.group()
        assert case != 'error'
        if case == 'python':
            python_list = [group]
            while 1:
                t = next(tokens)
                python_list.append(t.group())
                if t.lastgroup == 'end' and t.group() == end(group):
                    python = ''.join(python_list)
                    try:
                        ast.parse(python+'\n\n', mode='eval')
                    except SyntaxError as se:
                        if 'EOL' in se.msg or 'EOF' in se.msg:
                            continue  # Not complete yet.
                        raise
                    else:
                        yield 'python', python
                        break
        elif case in IGNORE:
            pass
        elif case == 'indent':
            width = len(group)
            if width > indents[-1]:
                indents.append(width)
            elif width < indents[-1]:
                while width < indents[-1]:
                    indents.pop()
                    opens -= 1
                    yield 'close', ']DEDENT]'
            while opens >= len(indents):
                opens -= 1
                yield 'close', ']EQDENT]'
        elif case == 'polyadic':
            opens += 1
            yield 'open', '{{'
            if group != '::':
                yield case, group[:-1]
        elif case == 'unary':
            yield case, group[:-1]
        elif case == 'eol':
            while opens-1 > len(indents):
                opens -= 1
                yield 'close', ']EOL]'
        else:
            yield case, group

    while opens:
        opens -= 1
        yield 'close', ']EOF]'


def _parse(tokens):
    tokens = iter(tokens)
    for case, group in tokens:
        if case == 'open':
            yield (*_parse(tokens),)
        elif case == 'close':
            return
        elif case == 'unary':
            if group == ':':
                yield next(_parse(tokens)),
            else:
                yield group, next(_parse(tokens)),
        elif case == 'symbol':
            if group.isidentifier():
                yield group
            else:
                yield ast.literal_eval(group)
        else:
            yield group

code = "a"
"""
a: x: y:
  b: z:
    c:
"""
"""
::
z:a: b: c: d : e f
  e
"""
"""
for: x :in range:3
  q
  print: x (
  print(x)
)
"""

for k,v in lex(code):
    print(k, repr(v))

from pprint import pprint
pprint([*_parse(lex(code))])

print('DONE')