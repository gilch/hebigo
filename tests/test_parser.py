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
""": [('for', 'x', ':in', ('range',3,),'q',('print','x','''(\
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

'operator..getitem:::globals':[('operator..getitem',('globals',))],
}

class TestParser(TestCase):
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
