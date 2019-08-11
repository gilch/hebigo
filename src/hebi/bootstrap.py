import ast


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
