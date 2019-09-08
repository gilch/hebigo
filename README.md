# Hebigo
蛇語(heh-bee-go): Snake-speak. An indentation-based skin for Hissp.

Hebigo is still in the prototyping phase. See the native tests for example Hebigo code.

Hebigo is a Hissp skin designed to resemble Python.

Hebigo's *bracketed expression* syntax is identical to Python's.
The compiler pretty much just injects it into the Python output.
All Python expressions must be "bracketed" somehow to be recognized as such.
Parentheses always work, but `[]` or `{}` are sufficient.
Quotation marks also work, even with prefixes, like `b''` or `f""""""`, etc.

However, Hebigo completely replaces Python's *statements* with "hotword expressions" with Hissp's semantics (and macros).

These resemble Python's statements in form, like
```
word:
   block1
   subword:
       subblock
   block2
```
etc.

The rules are as follows.

1. A word ending in a `:` is a "hotword", that is, an invocation that can take arguments.
```
hotword: not_hotword
```

2. A hotword with no whitespace after its colon is *unary*. Otherwise it's *multiary*.
```
unary:arg
multiary1: arg
multiary0:
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

4. The *first multiary* (**not** unary) hotword of the line gets the arguments in the indented block for that line.
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

5. The special hotword `pass:` uses its first argument for the invocation. This allows you to invoke things that are not words.
```
pass: foo a b
pass: (lambda *a: a) 1 2 3
```
Parsed like
```
foo(a, b)
(lambda *a: a)(1, 2, 3)
```
***
These indentation rules were designed to resemble Python and make editing easier with a basic editor than for s-expressions.
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
You should group arguments using whitespace when it makes sense to do so.
Usually after the `:`.
```
linear: x : a b  c d
linear_block:
    x : a b  c d
block:
    x
    :
    a b
    c d
```
Macro invocations are not exactly bound by these rules,
but may still have documented preferred layouts.
***
Hebigo does not munge symbols like Lissp does.
Qualified symbols (like ``builtins..print``) are allowed,
but not in bracketed expressions.
Also, "control words" are words that start with a `:`.
These are not allowed in bracketed expressions either
(although they're just compiled to strings, which are).
You'll need these for paired arguments, same as Lissp.
These two expressions are equivalent in Hebigo.
```
print: 1 2 3 : :* 'abc'  sep "/"  # Hotword expression.
(print(1, 2, 3, *'abc', sep="/"))  # Bracketed expression.
```
They would not be the same if `print` were a macro.

Control words may also be used as hotwords.
This makes no sense at the top level (because strings are not callable), but macros do use them to group arguments.

Hotword expressions may contain bracketed expressions, but not the reverse, since bracketed expressions must be valid Python,
just like how the statements that the hotword expressions replace may contain expressions,
but Python expressions may not contain Python statements.

And finally, the `!` is an abbreviation for `hebi.basic.._macro_.`. Hebigo has no other "reader macros".
