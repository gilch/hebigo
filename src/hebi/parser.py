import ast
import os
import re
from contextlib import contextmanager
from contextvars import ContextVar
from importlib import resources
from pathlib import PurePath, Path
from pprint import pprint
from types import ModuleType
from typing import Union

from hissp import compiler

TOKEN = re.compile(r"""(?x)
 (?P<end>[)\]}])
|(?P<comment>\n?[ ]*[#].*)
|(?P<indent>(?<=\n)[ ]*(?=[^\r\n]))
|(?P<empty>\([ \r\n]*\))
|(?P<python>[([{]|(?:[rR][bfBF]?|[bfBF][rR]?|[uU])?(?:'''|["]""|['"]))
|(?P<blank>\r?\n)
|(?P<sp>[ ])
|(?P<eol>(?<=\n))

# Hotwords
|(?P<unary>(?:
    !?  # basic macro?
    [.\w]+  # unary symbol
    |:[^ \r\n"')\]}]*  # unary control word
    ):(?=[^ \r\n]))  # lack of space after ending colon makes it unary
|(?P<multiary>(?:
    !?  # basic macro?
    [.\w]+  # multiary symbol
    |:[^ \r\n"')\]}]*  # multiary control word
    ):(?=[ \r\n]))  # space after ending colon makes in multiary

|(?P<controlword>:[^ \r\n"')\]}]*)
|(?P<symbol>[^ \r\n"')\]}]+)
|(?P<error>.|\n)
""")


def end(s):
    for q in ['"""', "'''", "'", '"']:
        if q in s:
            return q
    return {'(': ')', '[': ']', '{': '}'}[s]


IGNORE = frozenset({
    'comment',
    'sp',
    'blank',
})


def lex(code):
    """
    Because Hebigo is context sensitive, the lexer has to do extra work.
    It keeps an indentation stack and a count of open hot word forms,
    so it can infer when to close them.

    The language rules also change when inside a Python expression.
    Rather than re-implementing Python's complex grammar, the lexer
    just defers to Python's parser to determine if an expression
    that might have been completed has been.

    """
    opens = 0
    indents = [0]
    tokens = iter(TOKEN.finditer(code + '\n'))
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
                        ast.parse(python + '\n\n', mode='eval')
                    except SyntaxError as se:
                        if 'EOL' in se.msg or 'EOF' in se.msg:
                            continue  # Token not complete yet.
                        raise
                    else:
                        yield 'python', python
                        break
        elif case in IGNORE:
            pass
        elif case == 'indent':
            width = len(group)
            if width > indents[-1]:
                if len(indents) > opens:
                    ie = IndentationError("New indent in same block.")
                    ie.text = code[:code.find('\n', token.span()[1])]
                    ie.lineno = ie.text.count('\n')
                    raise ie
                indents.append(width)
            elif width < indents[-1]:
                while width < indents[-1]:
                    indents.pop()
                    opens -= 1
                    yield 'close', 'DEDENT'
            while opens >= len(indents):
                opens -= 1
                yield 'close', 'EQDENT'
        elif case == 'multiary':
            opens += 1
            yield 'open', ':'
            if group != 'pass:':
                yield case, group[:-1]
        elif case == 'unary':
            yield case, group[:-1]
        elif case == 'eol':
            while opens - 1 > len(indents):
                opens -= 1
                yield 'close', 'EOL'
        else:
            yield case, group

    while opens:
        opens -= 1
        yield 'close', 'EOF'


RESERVED_WORDS = frozenset(
    {'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def',
     'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if',
     'import', 'in', 'is', 'nonlocal', 'not', 'or', 'raise', 'return',
     'try', 'while', 'with', 'yield'})


def parse(tokens):
    tokens = iter(tokens)
    for case, group in tokens:
        if group in RESERVED_WORDS:
            group = f"hebi.basic.._macro_.{group}_"
        elif group.startswith('!'):
            group = f"hebi.basic.._macro_.{group[1:]}"
        if case == 'open':
            yield (*parse(tokens),)
        elif case == 'close':
            return
        elif case == 'unary':
            if group == 'pass':
                yield next(parse(tokens)),
            else:
                yield group, next(parse(tokens)),
        elif case == 'symbol':
            if all(s.isidentifier() for s in group.split('.') if s):
                yield group
            else:
                yield ast.literal_eval(group)
        elif case == 'python':
            # Parentheses let the compiler know it's Python expression code.
            yield f"({group})"
        else:
            yield group


def reads(hebigo):
    res = parse(lex(hebigo))
    return res


def transpile(package: resources.Package, *modules: Union[str, PurePath]):
    for module in modules:
        transpile_module(package, module + ".hebi")


QUALSYMBOL = ContextVar("QUALSYMBOL", default=None)


@contextmanager
def qualify_context(qualname):
    token = QUALSYMBOL.set(qualname)
    try:
        yield
    finally:
        QUALSYMBOL.reset(token)


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
        with open(out, "w") as f, qualify_context(f"{package}.{resource.split('.')[0]}") as qualsymbol:
            print("writing to", out)
            hissp = parse(lex(code))
            f.write(compiler.Compiler(qualsymbol, evaluate=True).compile(hissp))


code = '''\
test_default_strs lambda: self:
    self.assertEqual:
        ['ab', 22, 33]
        !let:
            :=: :strs: a b c
                :default: a ('a'+'b')
            {'b':22,'c':33}
            [a, b, c]
'''

for k, v in lex(code):
    print(k, repr(v))


pprint(list(reads(code)))

print('DONE')
