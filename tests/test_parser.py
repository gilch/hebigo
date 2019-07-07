from unittest import TestCase

from hebi.parser import lex, _parse

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
""": [('for', 'x', ':in', ('range',3,),'q',('print','x','''\
(
  print(x)
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
    ':: a ::b ::c': [('a',('b',),('c',),)]

}

class TestParser(TestCase):
    def test_examples(self):
        for k, v in EXPECTED.items():
            with self.subTest(code=k, parsed=v):
                print(k)
                lex_k = [*lex(k)]
                print(lex_k)
                parsed = [*_parse(lex_k)]
                print(parsed)
                self.assertEqual(parsed, v)
                print('OK')
