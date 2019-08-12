import ast
from itertools import islice, zip_longest


def def_(name, *body):
    """
    Assigns a global value or function in the current module.
    """
    if type(name) is tuple:
        name, *args = name
        doc = None
        if len(body) > 1 and _is_str(body[0]):
            doc, *body = body
        return (
            'hebi.basic.._macro_.def_',
            name,
            ('hebi.bootstrap..function', ('quote', name,), ('lambda', tuple(args), *body), doc),
        )
    if len(body) == 1:
        return (
            '.__setitem__',
            ('builtins..globals',),
            ('quote', name,),
            body[0]
        )
    raise SyntaxError


def _is_str(s):
    if type(s) is str:
        try:
            return type(ast.literal_eval(s)) is str
        except:
            pass


def function(name, fn, doc=None, qualname=None, annotations=None, dict_=()):
    """Enhances a Hissp lambda with function metadata.
    Assigns __doc__, __name__, __qualname__, and __annotations__.
    (__qualname__ is set to name if qualname is unspecified.)
    Then updates __dict__."""
    fn.__doc__ = doc
    fn.__name__ = name
    fn.__qualname__ = qualname or name
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
    return (('lambda',(),
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


def if_(condition, thunk, *pairs):
    """
    if: (a<b)
        ::
            print: "less"
        elif: (a>b)
            print: "more"
        elif: (a==b)
            print: "equal"
        else:
            print: "nan"
    """

    else_ = ()
    if pairs and pairs[-1][0] == 'hebi.basic.._macro_.else_':
        *pairs, else_ = pairs
        else_ = [
            ':','else_',('lambda',(),*else_[1:])
        ]

    elifs = []
    for pair in pairs:
        if pair[0] != 'hebi.basic.._macro_.elif_':
            raise SyntaxError(pair[0])
        elifs.extend([
            ('lambda',(),pair[1],),
            ('lambda',(),*pair[2:],)
        ])

    return (
        'hebi.bootstrap.._if_',
        condition,
        ('lambda',(),)+thunk,
        *elifs,
        *else_,
    )


_sentinel = object()


def _raise_():
    raise


def _raise_ex_(ex):
    raise ex


def _raise_ex_from_(ex, from_):
    raise ex from from_


def raise_(ex=None, key=_sentinel, from_=_sentinel):
    if ex:
        if key is not _sentinel:
            if key == ':from':
                return ('hebi.bootstrap.._raise_ex_from_', ex, from_,)
            else:
                raise SyntaxError(key)
        return ('hebi.bootstrap.._raise_ex_', ex)
    return ('hebi.bootstrap.._raise_')


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


def try_(block, *handlers):
    """
    try:
        ::
            print: "It's dangerous!"
            something_risky: thing
        except: LikelyProblemError
            print: "Oops!"
            fix_it:
        except: Exception :as ex
            do_something: ex
        else:
            print: "Hooray!"
            thing
        finally:
            .close: thing
    """
    thunk = ('lambda',(),) + block
    else_ = ()
    finally_ = ()
    except_ = []
    for handler in partition(handlers):
        if handler[0] == 'hebi.bootstrap..except_':
            if len(handler) > 3 and handler[2] == ':as':
                arg = handler[3]
                block_start = 4
            else:
                arg = 'xAUTO0_'
                block_start = 2
            except_.extend([handler[1], ('lambda',(arg,),*handler[block_start:],)])
        elif handler[0] == 'hebi.bootstrap..else_':
            if else_:
                raise SyntaxError(handler)
            else_ = ('lambda',(),handler[1:],),
        elif handler[0] == 'hebi.bootstrap..finally_':
            if finally_:
                raise SyntaxError(handler)
            finally_ = ('lambda',(),handler[1:],),
        else:
            raise SyntaxError(handler)
    return ('hebi.bootstrap.._try_',thunk,*except_,*else_,*finally_,)

