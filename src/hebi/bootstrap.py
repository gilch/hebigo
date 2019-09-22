# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import ast
import builtins
import re
from functools import wraps
from itertools import islice, zip_longest, chain, takewhile
from types import new_class

from hissp.compiler import NS

from hebi.parser import QUALSYMBOL

BOOTSTRAP = 'hebi.bootstrap..'


def _thunk(*args):
    return ('lambda', (), *args)


def _and_(expr, *thunks):
    result = expr
    for thunk in thunks:
        if not result:
            break
        result = thunk()
    return result


def and_(*args):
    if args:
        if len(args) == 1:
            return args[0]
        return (BOOTSTRAP + '_and_', args[0], *(
            _thunk(arg) for arg in args[1:]
        ))
    return True


def _or_(expr, *thunks):
    result = expr
    for thunk in thunks:
        if result:
            break
        result = thunk()
    return result


def or_(*args):
    if args:
        if len(args) == 1:
            return args[0]
        return (BOOTSTRAP + '_or_', args[0], *(
            _thunk(arg) for arg in args[1:]
        ))
    return ()


def _not_(b):
    return True if b else ()


def not_(expr):
    return BOOTSTRAP + '_not_', expr


def def_(name, *body):
    """
    Assigns a global value or function in the current module.
    """
    if type(name) is tuple:
        args, decorators, doc, ibody, name = destructure_decorators(name, body)
        return (
            'hebi.basic.._macro_.def_',
            name,
            _decorate(
                decorators,
                (BOOTSTRAP + 'function',
                 ('quote', name,),
                 ('lambda', tuple(args), *ibody),
                 doc)),
        )
    if len(body) == 1:
        name = _expand_ns(name)
        if '.' in name:
            ns, _, attr = name.rpartition('.')
            return (
                'builtins..setattr',
                ns,
                ('quote', attr),
                body[0],
            )
        return (
            '.__setitem__',
            ('builtins..globals',),
            ('quote', name,),
            body[0]
        )
    raise SyntaxError


def class_(name, *body):
    args, decorators, doc, ibody, name = destructure_decorators(name, body)
    return (
        'hebi.basic.._macro_.def_',
        name,
        _decorate(
            decorators,
            (BOOTSTRAP + '_class_',
             ('quote', name),
             (BOOTSTRAP + 'akword', *args),
             doc,
             ('.__getitem__', ('globals',), ('quote', '__name__'),),
             ('lambda',('__class__',),
              ('lambda',('_ns_',),
               '__class__',
               *ibody),),),
        )
    )


def destructure_decorators(name, body):
    name, *args = name
    doc = None
    decorators = []
    ibody = iter(body)
    for expr in ibody:
        if expr == ":@":
            decorators.append(next(ibody))
            continue
        if _is_str(expr):
            doc = expr
        else:
            ibody = expr, *ibody
        break
    name = _expand_ns(name)
    return args, decorators, doc, ibody, name


def akword(*args, **kwargs):
    return args, kwargs


def _class_(name, args, doc, module, callback):
    callback = callback(None)
    def exec_callback(ns):
        ns['__module__'] = module
        if doc is not None:
            ns['__doc__'] = doc
        callback(attrs(ns))
        return ns

    bases, kwds = args
    cls = new_class(name, bases, kwds, exec_callback)
    # new_class() isn't setting super()'s __class__ cell for some reason.
    # Not sure if it's always this easy to find the right cell.
    assert len(callback.__closure__) == 1
    callback.__closure__[0].cell_contents = cls
    return cls


def _decorate(decorators, callable):
    for decorator in reversed(decorators):
        callable = _expand_ns(decorator), callable
    return callable


def _expand_ns(name):
    if type(name) is tuple:
        return (_expand_ns(name[0]), *name[1:])
    if type(name) is str and name.startswith('.'):
        name = '_ns_' + name
    return name


def _is_str(s):
    if type(s) is str:
        try:
            return type(ast.literal_eval(s)) is str
        except:
            pass


def function(qualname, fn, doc=None, annotations=None, dict_=()):
    """Enhances a Hissp lambda with function metadata.
    Assigns __doc__, __name__, __qualname__, and __annotations__.
    Then updates __dict__."""
    fn.__doc__ = doc
    fn.__name__ = qualname.split('.')[-1]
    fn.__qualname__ = qualname
    fn.__annotations__ = annotations or {}
    fn.__dict__.update(dict_)
    return fn


def import_(*specs):
    pairs = []
    specs = iter(specs)
    for spec in specs:
        if spec != ":as":
            pairs.append([spec.split('.')[0], spec])
        else:
            pairs[-1][0] = next(specs)
    return (_thunk(
             *(('.__setitem__',
                ('builtins..globals',),
                ('quote',k),
                ('__import__',
                 ('quote',v),
                 ('builtins..globals',),),)
               for k, v in pairs),),)


def from_(name, import_, *specs):
    if import_ != ':import':
        raise SyntaxError
    fromlist = []
    pairs = []
    specs = iter(specs)
    for spec in specs:
        if spec != ":as":
            pairs.extend([spec, 'module.' + spec])
            fromlist.append(spec)
        else:
            pairs[-2] = next(specs)
    sname = name.lstrip('.')
    return (('lambda',('module',),
             ('.update',
              ('builtins..globals',),
              ('dict',':',*pairs),),),
            ('__import__',
             ('quote',sname),
             ':',
             'globals',('builtins..globals',),
             'fromlist',fromlist,
             'level',len(name)-len(sname),),)


def _if_(b, thunk, *elifs, else_=lambda:()):
    if b:
        return thunk()
    elifs = iter(elifs)
    for elif_ in elifs:
        if elif_():
            return next(elifs)()
    return else_()


def if_(condition, then, *pairs):
    """
    if: (a<b)
        :then:
            print: "less"
        :elif: (a>b)
            print: "more"
        :elif: (a==b)
            print: "equal"
        :else:
            print: "nan"
    """

    else_ = ()
    if pairs and pairs[-1][0] == ':else':
        *pairs, else_ = pairs
        else_ = [
            ':','else_',_thunk(*else_[1:])
        ]

    elifs = []
    for pair in pairs:
        if pair[0] != ':elif':
            raise SyntaxError(pair[0])
        elifs.extend([
            _thunk(pair[1],),
            _thunk(*pair[2:],)
        ])

    if then[0] != ':then':
        raise SyntaxError(then)

    return (
        BOOTSTRAP + '_if_',
        condition,
        _thunk(*then[1:]),
        *elifs,
        *else_,
    )


_sentinel = object()


def _raise_():
    raise


def _raise_ex(ex):
    raise ex


def _raise_ex_from(ex, from_):
    raise ex from from_


def raise_(ex=None, key=_sentinel, from_=_sentinel):
    if ex:
        if key is not _sentinel:
            if key == ':from':
                return BOOTSTRAP + '_raise_ex_from', ex, from_,
            else:
                raise SyntaxError(key)
        return BOOTSTRAP + '_raise_ex', ex
    return BOOTSTRAP + '_raise'


def partition(iterable, n=2, step=None, fillvalue=_sentinel):
    """
    Chunks iterable into tuples of length n. (default pairs)
    >>> list(partition(range(10)))
    [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]

    The remainder, if any, is not included.
    >>> list(partition(range(10), 3))
    [(0, 1, 2), (3, 4, 5), (6, 7, 8)]

    Keep the remainder by using a fillvalue.
    >>> list(partition(range(10), 3, fillvalue=None))
    [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9, None, None)]
    >>> list(partition(range(10), 3, fillvalue='x'))
    [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 'x', 'x')]

    The step defaults to n, but can be more to skip elements.
    >>> list(partition(range(10), 2, 3))
    [(0, 1), (3, 4), (6, 7)]

    Or less for a sliding window with overlap.
    >>> list(partition(range(5), 2, 1))
    [(0, 1), (1, 2), (2, 3), (3, 4)]
    """
    step = step or n
    slices = (islice(iterable, start, None, step) for start in range(n))
    if fillvalue is _sentinel:
        return zip(*slices)
    else:
        return zip_longest(*slices, fillvalue=fillvalue)


def _try_(thunk, *except_, else_=None, finally_=lambda:()):
    if not all(isinstance(x, tuple)
               or issubclass(x, BaseException)
               for x, c in partition(except_)):
        raise TypeError
    try:
        res = thunk()
    except BaseException as ex:
        for ex_type, ex_handler in partition(except_):
            if isinstance(ex, ex_type):
                return ex_handler(ex)
        else:
            raise
    else:
        if else_:
            res = else_()
    finally:
        finally_()
    return res


def try_(expr, *handlers):
    """
    try:
        !begin:
            print: "It's dangerous!"
            something_risky: thing
        :except: LikelyProblemError
            print: "Oops!"
            fix_it:
        :except: Exception :as ex
            do_something: ex
        :else:
            print: "Hooray!"
            thing
        :finally:
            .close: thing
    """
    else_ = ()
    finally_ = ()
    except_ = []
    for handler in handlers:
        if handler[0] == ':except':
            if len(handler) > 3 and handler[2] == ':as':
                arg = handler[3]
                block_start = 4
            else:
                arg = 'xAUTO0_'
                block_start = 2
            except_.extend([handler[1], ('lambda',(arg,),*handler[block_start:],)])
        elif handler[0] == ':else':
            if else_:
                raise SyntaxError(handler)
            else_ = 'else_', _thunk(*handler[1:]),
        elif handler[0] == ':finally':
            if finally_:
                raise SyntaxError(handler)
            finally_ = 'finally', _thunk(*handler[1:]),
        else:
            raise SyntaxError(handler)
    return (BOOTSTRAP + '_try_', _thunk(expr), *except_, ':', *else_, *finally_,)


def mask(form):
    case = type(form)
    if case is tuple and form:
        if _is_str(form):
            return 'quote', form
        if form[0] == ':,':
            return form[1]
        if form[0] == 'hebi.basic.._macro_.mask':
            return mask(mask(form[1]))
        return (
            BOOTSTRAP + 'entuple', ':', *chain.from_iterable(_mask(form)),
        )
    if case is str and not form.startswith(':'):
        return 'quote', _qualify(form)
    return form


def _mask(forms):
    for form in forms:
        case = type(form)
        if case is str and not form.startswith(':'):
            yield ':?', ('quote', _qualify(form))
        elif case is tuple and form:
            if form[0] == ':,':
                yield ':?', form[1]
            elif form[0] == ':,@':
                yield ':*', form[1]
            elif form[0] == 'hebi.basic.._macro_.mask':
                yield ':?', mask(mask(form[1]))
            else:
                yield ':?', mask(form)
        else:
            yield ':?', form


def _qualify(symbol):
    if symbol.startswith('('):
        return symbol
    if symbol in {e for e in dir(builtins) if not e.startswith('_')}:
        return f'builtins..{symbol}'
    if re.search(r"\.\.|^\.|^quote$|^lambda$|xAUTO\d+_$", symbol):
        return symbol
    qualname = QUALSYMBOL.get()
    if qualname:
        if symbol in vars(NS.get().get("_macro_", lambda: ())):
            return f"{qualname}.._macro_.{symbol}"
        return f"{qualname}..{symbol}"
    return symbol


def _begin(*body):
    return body and body[-1]


def begin(*body):
    return (BOOTSTRAP + '_begin', *body)


def _begin0(zero, *body):
    return zero


def begin0(*body):
    return (BOOTSTRAP + '_begin0', *body)


def _with_(guard, body):
    with guard() as g:
        return body(g)


def with_(guard, *body):
    """
    with: foo:bar :as baz
        frobnicate: baz
    """
    if len(body) > 2 and body[1] == ':as':
        return BOOTSTRAP + '_with_', _thunk(guard), ('lambda',(body[2],),*body[3:]),
    return BOOTSTRAP + '_with_', _thunk(guard), ('lambda',('xAUTO0_',),*body),


def _assert_(b):
    assert b


def _assert_message(b, thunk):
    assert b, thunk()


def assert_(b, *message):
    if message:
        return BOOTSTRAP + '_assert_', b
    return BOOTSTRAP + '_assert_message', b, _thunk(*message)


def _flatten_tuples(expr):
    if expr[0] == ':=':
        yield from _flatten_mapping(iter(expr))
    else:
        for e in expr:
            if type(e) is tuple:
                yield from _flatten_tuples(e)
            elif (
                type(e) is str
                and e != '_'
                and not e.startswith('(')
                and not e.startswith(':')
            ):
                yield e


def _flatten_mapping(expr):
    head = next(expr)
    assert head == ':='
    for e in expr:
        if type(e) is tuple:
            if e[0] == ':default':
                continue
            if e[0] == ':strs':
                yield from _flatten_tuples(e)
                continue
        if e == ':as':
            yield next(expr)
            continue
        yield from _flatten_tuples(e)
        next(expr)


def _unpack(target, value):
    if type(target) is tuple and target:
        if target[0] == ':,':
            yield from _unpack_iterable(target, value)
        if target[0] == ':=':
            yield from _unpack_mapping(target, value)
    elif target == '_':
        pass
    else:
        yield value


def _unpack_iterable(target, value):
    ivalue = iter(value)
    itarget = iter(target)
    head = next(itarget)
    assert head == ':,'
    for t in itarget:
        if t == ':list':
            yield from _unpack(next(itarget), list(ivalue))
        elif t == ':iter':
            yield from _unpack(next(itarget), ivalue)
        elif t == ':as':
            yield from _unpack(next(itarget), value)
        else:
            yield from _unpack(t, next(ivalue))


def _unpack_mapping(target, value):
    itarget = iter(target)
    head = next(itarget)
    assert head == ':='
    for t in target:
        if type(t) is tuple and t[0] == ':default':
            default = dict(partition(t[1:]))
            break
    else:
        default = {}
    for t in itarget:
        if t == ':as':
            next(itarget)
            yield value
        elif type(t) is tuple and t[0] == ':strs':
            for s in t[1:]:
                try:
                    yield value[s]
                except LookupError:
                    yield default[s]
        elif type(t) is tuple and t[0] == ':default':
            continue
        else:
            try:
                yield from _unpack(t, value[next(itarget)])
            except LookupError:
                yield default[t]


def _quote_tuple(target):
    head = next(target)
    yield 'quote', head
    for t in target:
        if type(t) is tuple:
            if head == ':=' and t[0] == ':strs':
                yield 'quote', t
            elif head == ':=' and t[0] == ':default':
                yield _quote_target(t)
            else:
                yield _quote_target(t)
                if head == ':=':
                    yield next(target)
        elif head in ':=' and type(t) is str and t.startswith(':'):
            yield t
            t = next(target)
            if type(t) is tuple:
                yield _quote_target(t)
            else:
                yield 'quote', t
        else:
            yield 'quote', t
            if head in {':=', ':default'}:
                yield next(target)


def _quote_target(target):
    return (BOOTSTRAP + 'entuple', *_quote_tuple(iter(target)))


def let(target, be, value, *body):
    if be != ':be':
        raise SyntaxError('Missing :be in !let.')
    if type(target) is tuple:
        parameters = tuple(_flatten_tuples(target))
        return (
            ('lambda', parameters, *body),
            ':', ':*', (BOOTSTRAP + '_unpack', _quote_target(target), value,),
        )
    return ('lambda',(target,),*body,), value,


def entuple(*xs):
    return xs

def _loop(f):
    again = False

    def recur(*args, **kwargs):
        nonlocal again
        again = True
        # The recursion thunk.
        return lambda: f(recur, *args, **kwargs)

    @wraps(f)
    def wrapper(*args, **kwargs):
        nonlocal again
        res = f(recur, *args, **kwargs)
        while again:
            again = False
            res = res()  # when recur is called it must be returned!
        return res

    return wrapper


def loop(start, *body):
    """
    !loop: recur: xs 'abc'  ys ''
        if: xs :then: recur(xs[:-1], ys+xs[-1])
            :else: ys
    """
    return (
        BOOTSTRAP + '_loop',
        ('lambda',(start[0],':',*start[1:],),
         *body),
    ),


class LabeledBreak(BaseException):
    def handle(self, label=None):
        """ re-raise self if label doesn't match. """
        if self.label is None or self.label == label:
            return
        else:
            raise self

    def __init__(self, label=None):
        self.label = label
        raise self


class LabeledResultBreak(LabeledBreak):
    def __init__(self, result=None, *results, label=None):
        if results:
            self.result = (result,) + results
        else:
            self.result = result
        LabeledBreak.__init__(self, label)


class Break(LabeledResultBreak):
    pass


def break_(*args):
    if args and args[0] and args[0].startswith(':'):
        return (BOOTSTRAP + 'Break', *args[1:], ':', 'label', args[0])
    return (BOOTSTRAP + 'Break', *args)


class Continue(LabeledBreak):
    pass


def continue_(label=None):
    return BOOTSTRAP + 'Continue', label


def _for_(iterable, body, else_=lambda:(), label=None):
    try:
        for e in iterable:
            try:
                body(e)
            except Continue as c:
                c.handle(label)
    except Break as b:
        b.handle(label)
        # skip else_() on Break
        return b.result
    return else_()


def for_(*exprs):
    label = 'label', None,
    else_ = ()
    if type(exprs[-1]) is tuple and exprs[-1] and exprs[-1][0] == ':else':
        else_ = 'else_', _thunk(*exprs[-1][1:])
        exprs = exprs[:-1]
    iexprs = iter(exprs)
    if type(exprs[0]) is str and exprs[0].startswith(':'):
        label = 'label', exprs[0],
        next(iexprs)
    *bindings, = takewhile(lambda a: a != ':in', iexprs)
    iterable = next(iexprs)
    *body, = iexprs
    if body and type(body[-1]) is tuple and body[-1] and body[-1][0] == ':else':
        else_ = 'else_', body.pop()[1:]
    if type(bindings[0]) is str:
        body = (tuple(bindings), *body)
    else:
        body = ('xAUTO0_',), ('hebi.basic.._macro_.let', *bindings, ':be', 'xAUTO0_', *body),
    return (
        BOOTSTRAP + '_for_',
        iterable,
        ('lambda', *body),
        ':',
        *else_,
        *label,
    )


def runtime(*forms):
    return ('hebi.basic.._macro_.if_', "(__name__!='<compiler>')",
            (':then', *forms))


class attrs(object):
    """
    Attribute view proxy of a mapping.

    Provides Lua-like syntactic sugar when the mapping has string
    keys that are also valid Python identifiers, which is a common
    occurrence in Python, for example, calling vars() on an object
    returns such a dict.

    Unlike a SimpleNamespace, an attrs proxy doesn't show the extra
    magic attrs from the class, and it can write through to any type of
    mapping.

    >>> spam = {}
    >>> atspam = attrs(spam)

    get and set string keys as attrs
    >>> atspam.one = 1
    >>> atspam.one
    1
    >>> atspam
    attrs({'one': 1})

    changes write through to underlying dict
    >>> spam
    {'one': 1}

    calling the object returns the underlying dict for direct access
    to all dict methods and syntax
    >>> list(
    ...  atspam().items()
    ... )
    [('one', 1)]
    >>> atspam()['one'] = 42
    >>> atspam()
    {'one': 42}

    del removes the key
    >>> del atspam.one
    >>> atspam
    attrs({})
    """

    __slots__ = "mapping"

    def __init__(self, mapping):
        object.__setattr__(self, "mapping", mapping)

    def __call__(self):
        return object.__getattribute__(self, "mapping")

    def __getattribute__(self, attr):
        try:
            return self()[attr]
        except KeyError as ke:
            raise AttributeError(*ke.args)

    def __setattr__(self, attr, val):
        self()[attr] = val

    def __delattr__(self, attr):
        try:
            del self()[attr]
        except KeyError as ke:
            raise AttributeError(*ke.args)

    def __repr__(self):
        return "attrs(" + repr(self()) + ")"

