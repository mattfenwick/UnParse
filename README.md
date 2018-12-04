## UnParse ##

Another parser combinator library for Python!

UnParse is opinionated!

 - simple and clear definition of the parse model:
   - inputs
   - outputs
   - backtracking
   - (non)-deterministic 
   - prioritized choice
 
 - no magic

 - doesn't hide important details -- but also doesn't force you to worry about
   them unless you need to

 - provides complex parsers as well as the primitives
 
 - compositional semantics -- it's easy to make big parsers by combining lots of smaller parsers;
   parser behavior is not affected by context
   
 - doesn't treat lexing as a special case (but allows you to if you want to)

 - powerful combinators for building trees matching the structure of the grammar

 - first class error generation and handling

Read on for more information!
 

## Overview ##

UnParse is a library for building complex parsers.  Parsers are created and
manipulated as Python objects, and are invoked using their `parse` method,
which takes two arguments:

 - the token sequence that is being parsed
 - the parsing state

The return value is one of three possible results:

 - success, including:
    - the remaining tokens
    - new state
    - result value
 - failure, which indicates that the match failed
 - error, which means that something bad happened and includes error information

Successful parses allow parsing to continue; failures allow parsing to backtrack
and try a different alternative; errors abort parsing immediately with relevant
error information to accurately indicate what and where the problem was.

UnParse supports monadic parsing, as well as combinators based on the Applicative,
Functor, MonadError, Alternative, and Traversable typeclasses, if you're familiar
with Haskell.  It also supports lookahead and optional parses.  

Best of all, since parsers are ordinary Python objects, they play by the rules --
you don't need any special knowledge or syntax to use them, they work just fine
with functions and classes, and you can put them in data structures.

UnParse avoids magic -- the kind of magic that makes it easy to do really simple
things, but hard to deal with actual real-world problems in a clean, sane way.
This allows UnParse to stay simple and focused -- and you don't need to worry 
about it mucking with things behind your back -- and free of arbitrary restrictions.
     

### Contact information ###

Found a bug?  Need help figuring something out?  Want a new feature?  Feel free
to report anything using the github issue tracker or open a PR!
