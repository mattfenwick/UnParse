## UnParse ##

A parser combinator library for Python.
 

## Overview ##

UnParse is a library for building complex parsers.  Parsers are created and
manipulated as Python objects, and are invoked using their `parse` method,
which takes two arguments:

 - the token sequence that is being parsed
 - the parsing state

The return value is one of three possible results:

 - success, in which case it includes the (possibly modified) token sequence,
   the (possibly modified) parsing state, and a result
 - failure, which indicates that the match failed
 - error, which means that something bad happened which needs to be reported --
   it includes error information

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

Enjoy!


## API ##

 - `Parser` -- parameterized by an underlying result type
 
   1. static methods/values
   
     - `pure`
     
     - `error`
     
     - `zero`
     
     - `item`
     
     - `app`
     
     - `satisfy`
     
     - `all`
     
     - `literal`
     
     - `string`
     
     - `put`
     
     - `get`
     
     - `putState`
     
     - `getState`
     
     - `updateState`
     
     - `any`
   
   2. instance methods
   
     - `fmap`
     
     - `bind`
     
     - `plus`
     
     - `mapError`
     
     - `check`
     
     - `many0`
     
     - `many1`
     
     - `optional`
     
     - `seq2L`
     
     - `seq2R`
     
     - `not0`
     
     - `not1`

     - `commit`
     

### Contact information ###

Found a bug?  Need help figuring something out?  Want a new feature?  Feel free
to report anything using the github issue tracker, or email me directly at
mfenwick100 at gmail dot com
