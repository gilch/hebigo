[![Gitter](https://badges.gitter.im/hissp-lang/community.svg)](https://gitter.im/hissp-lang/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
# Hebigo
蛇語(HEH-bee-go): Snake-speak.
Hebigo is an indentation-based [Hissp](https://github.com/gilch/hissp) skin designed to resemble Python.

It includes the Hebigo Hissp reader, the Jupyter-console based Hebigo REPL,
and the Hebigo basic macros—a collection of Python-like compiler macros,
which also function independently of the Hebigo reader
(i.e. they work in Lissp or Hissp readerless mode as well).

Hebigo is still in the prototyping phase, so it's not on PyPI yet.
Install it directly from GitHub with
```
pip install git+https://github.com/gilch/hebigo
```
See the native tests for example Hebigo code.

Hebigo keeps Python's expressions as *bracketed expressions*,
but completely replaces Python's *statements* with *hotword expressions*,
which have Hissp's literals, semantics, and macros.

## Bracketed Expressions
Bracketed expression are called that because they must be "bracketed"
somehow in order to be distinguishable from the hotword expressions.
Parentheses will always work, but `[]` or `{}` are sufficient.
Quotation marks also work, even with prefixes, like `b''` or `f""""""`, etc.

Bracketed expressions are mainly used for infix operators, simple literals, and f-strings
(things that might be awkward as hotword expressions),
but any Python expression will work,
even more complex ones like nested comprehensions or chained method calls.
It's best to keep these simple though.
You can't use macros in them.

## Hotword Expressions
Hotword expressions are called expressions because they evaluate to a value,
but they resemble Python's statements in form:
```
word:
   block1
   subword:
       subblock
   block2
```
etc.

The rules are as follows.

1. A word ending in a `:` is a "hotword", that is, a function or macro invocation that can take arguments.
```
hotword: not_hotword
```

2. A hotword with no whitespace after its colon is *unary*. Otherwise it's *multiary*.
```
unary:arg
multiary0:
multiary1: arg
multiary2: a b
multiary3: a b c
```

3. Multiary hotwords take all remaning arguments in a line.
```
hotword: arg1 arg2 arg3: a:0 b: 1 2
```
Parsed like
```
hotword(arg1, arg2, arg3(a(0), b(1, 2)))
```

4. The first (multiary) hotword of the line gets the arguments in the indented block for that line (if any).
```
multiary: a b c
    d e f
foo unary:gets_block: gets_line: 1 2
    a b
    c d
```
Parsed like
```
multiary(a, b, c, d, e, f)
foo
unary(gets_block(gets_line(1, 2), a, b, c, d))
```
Another way to think of it is that a unary applied to another hotword creates a *compound hotword*, which is a composition of the functions.
In the example above, `foo` is not a hotword (no colon),
and the compound hotword `unary:gets_block:` is the first hotword of the line,
so it gets the indented block below the line.

5. The special hotword `pass:` invokes its first argument, passing it the remainder.
This allows you to invoke things that are not words, like lambda expressions:
```
pass: foo a b
pass: (lambda *a: a) 1 2 3
```
Parsed like
```
foo(a, b)
(lambda *a: a)(1, 2, 3)
```
### Style
These indentation rules were designed to resemble Python and make editing easier with a basic editor than for S-expressions.
As a matter of style, arguments should be passed in one of three forms, which should not be mixed for function calls.
```
linear: a b c d
linear_block:
    a b c d
block:
    a
    b
    c
    d
# What NOT to do, although it compiles fine.
bad_mix: a
   b c
   d
```
compare that to the same layout for Python invocations.
```
linear(a, b, c, d)
linear_block(
    a, b, c, d
)
block(
    a,
    b,
    c,
    d,
)
# What NOT to do.
bad_mix(a,
    b, c
    d
)  # PEP 8 that. Please.
```
The above is for function calls only.
Macro invocations are not exactly bound by these three layout styles,
and may instead have other documented preferred layouts.

You should group arguments using whitespace when it makes sense to do so.
Anywhere you'd use a comma (or newline) in Clojure, you add an extra space or newline.
This usually after the `:` in function invocations or parameter tuples,
where the arguments are implicitly paired.
```
linear: x : a b  c d  # Note extra space between b and c.
linear_block:
    x : a b  c d
block:
    x
    : a b  # Newline also works.
    c d
```
### Literals
Literals are mostly the same as Lissp for hotword expressions
(and exactly like Python in bracketed expressions).

Hebigo does not munge symbols like Lissp does.
Qualified symbols (like ``builtins..print``) are allowed,
but not in bracketed expressions, which must be pure Python.

*Control words* are words that start with a `:`.
These are not allowed in bracketed expressions either
(although they're just compiled to strings, which are).
You'll need these for paired arguments, same as Lissp.
These two expressions are normally equivalent in Hebigo.
```
print: 1 2 3 : :* 'abc'  sep "/"  # Hotword expression.
(print(1, 2, 3, *'abc', sep="/"))  # Bracketed expression.
```
However, if a macro named `print` were defined,
then the hotword version would invoke the macro,
but the bracketed version would still invoke the builtin,
because macros can only be invoked in hotword expressions.

Control words may also be used as hotwords,
in which case they both begin and end with a colon.
This makes no sense at the top level (because strings are not callable),
but macros do use them to group arguments.

Unlike Lissp, normal string literals cannot contain literal newlines.
Use `\n` or triple quotes like Python instead.
(Recall that strings count as bracketed expressions.)

Hotword expressions may contain bracketed expressions,
but not the reverse, since bracketed expressions must be valid Python,
just like how the statements that the hotword expressions replace may contain expressions,
but Python expressions may not contain Python statements.

And finally, the `!` is an abbreviation for `hebi.basic.._macro_.`,
the qualifier for Hebigo's included macros.
(This can't work in bracketed expressions either.)
Hebigo has no other "reader macros".

## Examples

(Also see Hebigo's native tests.)

### Obligatory factorial example.

In basic Lissp. (Prelude assumed.)
```racket
(define factorial
  (lambda n
    (if-else (eq n 0)
      1
      (mul n (factorial (sub n 1))))))
```
Literal translation of the above to Hebigo.
```python
define: factorial
  lambda: n
    ifQz_else: eq: n 0
      1
      mul: n factorial: sub: n 1
```
Note the munged name.

In more ideomatic Hebigo with statement macros and bracketed expressions.
```python
def: factorial: n
  if: (n == 0)
    :then: 1
    :else: (n * factorial(n - 1))
```
Literal translation of the above to Lissp. (Statement macros required.)
```racket
(def_ (factorial n)
  (if_ .#"n == 0"
    (:then 1)
    (:else .#"n * factorial(n - 1)")))
```
Note the injections.

Finally, in ideomatic Lissp with Hebigo's macros.
```racket
(def_ (factorial n)
  (if-else (eq n 0)
    1
    (mul n (factorial (sub n 1)))))
```

### Fibonacci

In Python.
```python
from functools import lru_cache

@lru_cache(None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```
In Hebigo.
```python
def: fibonacci: n
  :@ functools..lru_cache: None  # Qualified identifier in decorator.
  if: (n <= 1)
    :then: n
    :else: (fibonacci(n - 1) + fibonacci(n - 2))
```
Literal translation to Lissp.
```racket
(def_ (fibonacci n)
  :@ (functools..lru_cache None) ; Qualified identifier in decorator.
  (if_ .#"n <= 1"
    (:then n)
    (:else .#"fibonacci(n - 1) + fibonacci(n - 2)")))
```
In basic Lissp.
```racket
(define fibonacci
  ((functools..lru_cache None) ; Callable expression.
   (lambda n
     (if-else (le n 1)
       n
       (add (fibonacci (sub n 1))
            (fibonacci (sub n 2)))))))
```
Literal translation to Hebigo
```python
define: fibonacci
  pass: functools..lru_cache: None  # Callable expression.
    lambda: n
      ifQz_else: le: n 1
        n
        add:
          fibonacci: sub: n 1
          fibonacci: sub: n 2
```
