# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittest import TestCase

from hebi.parser import lex, parse


EXPECTED = {
'':[],
'1':[1],
':foo':[":foo"],
':!@$%':[":!@$%"],
'1+1j':[1+1j],
'-1.3e5':[-1.3e5],

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
pass:
pass:
  z:a: b: c: d : e f
    e
""": [
    (),
    (('z',
      ('a',('b', ('c', 'd', ':', 'e', 'f'),),
       'e',),),),
],

'pass:a': [('a',)],
'pass:a pass:b pass:c': [('a',),('b',),('c',)],
'pass: a pass:b pass:c': [('a',('b',),('c',),)],

'foo: quux: spam': [('foo',('quux','spam'))],
'foo: pass: quux spam': [('foo',('quux','spam'))],
'foo: pass:quux spam': [('foo',('quux',),'spam')],

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
lambda: pass: name
    print: f"Hi, {name}!"
''':
   [
       ('lambda',('name',),
        ('print','(f"Hi, {name}!")',),)
   ],

'lambda: pass:name print: f"Hi, {name}!"':
    [
        ('lambda',('name',),
         ('print','(f"Hi, {name}!")',),)
    ],

'foo.bar..spam.eggs':['foo.bar..spam.eggs'],
'foo.bar..spam.eggs: toast':[('foo.bar..spam.eggs','toast')],
'foo.bar..spam.eggs:toast':[('foo.bar..spam.eggs','toast')],

'pass:pass:foo':[(('foo',),)],
'pass:pass:pass:foo':[((('foo',),),)],
'pass: pass: pass:foo':[((('foo',),),)],

'operator..getitem:pass:globals':[('operator..getitem',('globals',),)],

'''
nest: "foobar"
  .replace: "oo" "8"
  .upper:
''': [('nest','("foobar")',('.replace','("oo")','("8")',),('.upper',),)],
'''
nest: "foobar" pass:.upper .replace: "oo" "8"
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
"((greet('World') if __name__ == '__main__' else None))"],

'''
lambda: pass: x : :* a b
    print: x a
''': [('lambda',('x',':',':*','a','b'),
       ('print','x','a',),)],
'''\
!foo:bar
!spam: eggs
  !quux
if
!if_
''':[
    ('hebi.basic.._macro_.foo', 'bar'),
    ('hebi.basic.._macro_.spam', 'eggs', 'hebi.basic.._macro_.quux'),
    'hebi.basic.._macro_.if_',
    'hebi.basic.._macro_.if_',
],

'''
!mask:pass:lambda: :: :,:thing_sym :,:thing
    print: "Hi!"  # Builtin symbol.
    greet: "World!"  # Local symbol.
    :,@:map:  # Splice
        lambda: pass:call
            !mask:pass:  # Nested !mask.
                :,:operator..getitem: call 0
                :,:thing_sym
                :,@:operator..getitem: call slice: 1 None
        calls
    :,:thing_sym
''':[
('hebi.basic.._macro_.mask',
   (('lambda', (':', (':,', 'thing_sym'), (':,', 'thing')),
     ('print', '("Hi!")'),
     ('greet', '("World!")'),
     (':,@', ('map',
       ('lambda', ('call',),
        ('hebi.basic.._macro_.mask',
         ((':,', ('operator..getitem', 'call', 0)),
          (':,', 'thing_sym'),
          (':,@', ('operator..getitem', 'call', ('slice', 1, 'None')))))),
       'calls')),
     (':,', 'thing_sym')),))
],

'''
:=: :strs: a b c
    :default: a ('a'+'b')
''': [
(':=',
 (':strs', 'a', 'b', 'c'),
 (':default', 'a', "(('a'+'b'))"),
 )
],

'''
foo:
    [1, 2,
     3, 4]
    x
bar: 1
''': [
('foo',
 '([1, 2,\n     3, 4])',
 'x'),
('bar', 1),
],

'''
!mask:!mask::,::,:a
:foo:bar
:foo :bar
''': [
    ('hebi.basic.._macro_.mask',
     ('hebi.basic.._macro_.mask',
      (':,',
       (':,','a')))),
    (':foo','bar'),
    ':foo', ':bar',
]
}

BAD_INDENTS = ['''
# Missing colons.
test_default_strs lambda self:
    self.assertEqual:
        ['ab', 22, 33]
        !let
            :=: :strs: a b c
                :default: a ('a'+'b')
            {'b':22,'c':33}
            [a, b, c]
''',
'''
norlf:
    foo:
        [1, 2,
         3, 4]
         x  # Extra indent.
    y bar:
        1
''',
]
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

    def test_bad_indent(self):
        for e in BAD_INDENTS:
            with self.subTest(example=e):
                with self.assertRaises(IndentationError):
                    print([*lex(e)])
