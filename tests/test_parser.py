from unittest import TestCase

from hebi.parser import lex, parse


EXPECTED = {
'':[],
'a':['a'],
'\na':['a'],
'a\n':['a'],
'\na\n':['a'],
'a b c':['a','b','c'],

'''\
a
b
c
''':['a','b','c'],

'''\
a b
c
''':['a','b','c'],

'a:b': [('a','b')],
'a:': [('a',)],
'a: b': [('a','b')],
'a: b c': [('a','b','c')],

'''\
a:
  b
  c
''': [('a','b','c')],

'''\
a: b
  c
''': [('a','b','c')],

'''\
quote:a: b: c: d
  e
  :
  f g
''':[
    ('quote',
     ('a', ('b', ('c','d'),),
      'e',
      ':',
      'f','g'),)
],

"""\
for: x :in range:3
  q
  print: x (
  print(x)
)
""": [('hebi.basic.._macro_.for_', 'x', ':in', ('range',3,),'q',('print','x','''(\
(
  print(x)
)\
)''',),)],

"""\
a:
  b:
    c:
q
""": [('a',('b',('c',),),),'q'],

"""\
a: x: y:
  b: z:
    c:
""": [('a',('x',('y',),),('b',('z',),('c',),),)],

"""\
::
::
  z:a: b: c: d : e f
    e
""": [
    (),
    (('z',
      ('a',('b', ('c', 'd', ':', 'e', 'f'),),
       'e',),),),
],

'::a': [('a',)],
'::a ::b ::c': [('a',),('b',),('c',)],
':: a ::b ::c': [('a',('b',),('c',),)],

'foo: quux: spam': [('foo',('quux','spam'))],
'foo: :: quux spam': [('foo',('quux','spam'))],
'foo: ::quux spam': [('foo',('quux',),'spam')],

'print: "Hello, World!"': [('print', '("Hello, World!")',)],

'''
lambda: name:
    print: f"Hi, {name}!"
''':
    [
    ('lambda',('name',),
     ('print','(f"Hi, {name}!")',),)
    ],

'''
lambda: :: name
    print: f"Hi, {name}!"
''':
   [
       ('lambda',('name',),
        ('print','(f"Hi, {name}!")',),)
   ],

'lambda: ::name print: f"Hi, {name}!"':
    [
        ('lambda',('name',),
         ('print','(f"Hi, {name}!")',),)
    ],

'foo.bar..spam.eggs':['foo.bar..spam.eggs'],
'foo.bar..spam.eggs: toast':[('foo.bar..spam.eggs','toast')],
'foo.bar..spam.eggs:toast':[('foo.bar..spam.eggs','toast')],

'::::foo':[(('foo',),)],
'::::::foo':[((('foo',),),)],
':: :: ::foo':[((('foo',),),)],

'operator..getitem:::globals':[('operator..getitem',('globals',),)],

'''
nest: "foobar"
  .replace: "oo" "8"
  .upper:
''': [('nest','("foobar")',('.replace','("oo")','("8")',),('.upper',),)],
'''
nest: "foobar" ::.upper .replace: "oo" "8"
''': [('nest','("foobar")',('.upper',),('.replace','("oo")','("8")',),)],

'''
def: a 1
''': [('hebi.basic.._macro_.def_', 'a', 1,)],

'''
def: name: arg1 arg2 : kw1 default1
    "docstring"
    ...
''': [('hebi.basic.._macro_.def_',
       ('name', 'arg1', 'arg2', ':', 'kw1', 'default1',),
       '("docstring")',
       '...',)],

'quote:def': [('quote', 'hebi.basic.._macro_.def_',)],
'"def"': ['("def")'],
'quote:"def"': [('quote', '("def")',)],
'b"def"':['(b"def")'],

'''"""barfoo"""
''':['("""barfoo""")'],
'''
"""barfoo"""''':['("""barfoo""")'],
'''"""
foo
baz
"""''':['("""\nfoo\nbaz\n""")'],
'''
"""
foo
bar
"""
''':['("""\nfoo\nbar\n""")'],
'''
hot:
    block
()
''':[
    ('hot',
     'block'),
    '()'],
'''
hot:
    block
"spam"
''':[
    ('hot',
     'block'),
    '("spam")'],
'''
"""
docstring
"""
# comment

def: greet: name
    """Says Hi."""
    print: "Hello," name

# more commentary
(greet('World') if __name__ == '__main__' else None)
''':['("""\ndocstring\n""")',
('hebi.basic.._macro_.def_',('greet', 'name'),
  '("""Says Hi.""")',
  ('print', '("Hello,")', 'name')),
"((greet('World') if __name__ == '__main__' else None))"]
}

class TestParser(TestCase):
    def test_transpile(self):
        import tests.native_hebi_tests

    def test_examples(self):
        for k, v in EXPECTED.items():
            with self.subTest(code=k, parsed=v):
                print(k)
                lex_k = [*lex(k)]
                print(lex_k)
                parsed = [*parse(lex_k)]
                print(parsed)
                self.assertEqual(parsed, v)
                print('OK')
