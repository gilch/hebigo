import ast
import os
import re
from importlib import resources
from pathlib import PurePath, Path
from types import ModuleType
from typing import Union

from hissp import compiler

TOKEN = re.compile(r"""(?x)
 (?P<empty>\([ \r\n]*\))
|(?P<python>[([{]|(?:[rR][bfBF]?|[bfBF][rR]?|[uU])?(?:['"]|'''|["]""))
|(?P<end>[)\]{])
|(?P<comment>\n?[ ]*[#].*)
|(?P<indent>(?<=\n)[ ]*(?=[^\r\n]))
|(?P<blank>\r?\n)
|(?P<sp>[ ])
|(?P<eol>(?<=\n))
|(?P<unary>(?:\w+|:):(?=[^ \r\n]))
|(?P<polyadic>(?:\w+|:):(?=[ \r\n]))
|(?P<keysymbol>:\w*)
|(?P<keyword>and|as|assert|async|await|break
  |class|continue|def|del|elif|else|except|finally|for
  |from|global|if|import|in|is|lambda|nonlocal|not
  |or|pass|raise|return|try|while|with|yield)
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
                if (t.lastgroup in {'end', 'python'} and t.group() == end(group)):
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
                    yield 'close', 'DEDENT'
            while opens >= len(indents):
                opens -= 1
                yield 'close', 'EQDENT'
        elif case == 'polyadic':
            opens += 1
            yield 'open', ':'
            if group != '::':
                yield case, group[:-1]
        elif case == 'unary':
            yield case, group[:-1]
        elif case == 'eol':
            while opens-1 > len(indents):
                opens -= 1
                yield 'close', 'EOL'
        else:
            yield case, group

    while opens:
        opens -= 1
        yield 'close', 'EOF'


def parse(tokens):
    tokens = iter(tokens)
    for case, group in tokens:
        if case == 'open':
            yield (*parse(tokens),)
        elif case == 'close':
            return
        elif case == 'unary':
            if group == ':':
                yield next(parse(tokens)),
            else:
                yield group, next(parse(tokens)),
        elif case == 'symbol':
            if group.isidentifier():
                yield group
            else:
                yield ast.literal_eval(group)
        elif case == 'python':
            # Parentheses let the compiler know it's Python expression code
            yield f"({group})"
        else:
            yield group


def transpile(package: resources.Package, *modules: Union[str, PurePath]):
    for module in modules:
        transpile_module(package, module + ".hebi")


def transpile_module(
        package: resources.Package,
        resource: Union[str, PurePath],
        out: Union[None, str, bytes, Path] = None,
):
    code = resources.read_text(package, resource)
    path: Path
    with resources.path(package, resource) as path:
        out = out or path.with_suffix(".py")
        if isinstance(package, ModuleType):
            package = package.__package__
        if isinstance(package, os.PathLike):
            resource = resource.stem
        qualname = f"{package}.{resource.split('.')[0]}"
        with open(out, "w") as f:
            print("writing to", out)
            hissp = parse(lex(code))
            f.write(compiler.Compiler(qualname, evaluate=True).compile(hissp))


code = 'print: "Hello, World!"'

for k,v in lex(code):
    print(k, repr(v))

from pprint import pprint
pprint([*parse(lex(code))])

print('DONE')