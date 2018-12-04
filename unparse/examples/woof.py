#
# Woof  :=  Form(*)
#
# Form  :=  App     |  Special  |  List    |  
#           Symbol  |  Number   |  String
#
# App      :=  '('  Form(+)  ')'
#
# Special  :=  '{'  Symbol  Form(*)  '}'
#
# List     :=  '['  Form(*)  ']'
#
# Symbol   :=  [a-zA-Z_]  [a-zA-Z_0-9](*)
#
# Number   :=  \d(+)
#
# String   :=  '"'  ( char  |  escape )  '"'
#   where  char    :=  (not ( '\\'  |  '"'))
#          escape  :=  '\\'  ( '\\'  |  '"' )
#
# Comment  :=  ';'  (not '\n')(*)
#
# Whitespace  :=  /[ \t\n\r\f]/(+)
#
# any amount of whitespace or comments between tokens
#   (which are '(', ')', '{', '}', '[', ']', symbol, number, string
#

# This example demonstrates:
#   - tokenizing
#   - context-free parsing
#   - discarding any whitespace and comments without a separate lexing pass
#   - recursive grammar (must work around Python's non-let-rec binding)
#   - concrete parse tree construction
#   - position tracking (line/column)
#   - error reporting -- stack of errors

from ..cst import (node, cut)
from ..combinators import (position, seq2R, many0,
                           error,    alt,   seq2L, not0,
                           fmap,     many1, app)

(item, literal, satisfy) = (position.item, position.literal, position.satisfy)
(oneOf, not1, string) = (position.oneOf, position.not1, position.string)


WHITESPACE  = ' \t\n\r\f'
DIGITS      = '0123456789'
SYMBOLSTART = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
ESCAPES     = '\\"'

_comment = seq2R(literal(';'), 
                 many0(not1(literal('\n'))))

_whitespace = oneOf(WHITESPACE)

junk = many0(alt([_comment, _whitespace]))

_number = node('number', 
               ('digits', many1(oneOf(DIGITS))))

_symbol = node('symbol',
               ('first', oneOf(SYMBOLSTART)),
               ('rest', many0(oneOf(SYMBOLSTART + DIGITS))))

_char = node('char',
             ('value', not1(oneOf(ESCAPES))))

_escape = node('escape',
               ('open', literal('\\')),
               ('value', cut('\\ or double-quote', oneOf(ESCAPES))))

_string = node('string',
               ('open', literal('"')),
               ('body', many0(alt([_char, _escape]))),
               ('close', cut('double-quote', literal('"'))))

def tok(parser):
    return seq2L(parser, junk)

op, cp, os, cs, oc, cc = [tok(literal(c)) for c in '()[]{}']
symbol, number, string = map(tok, [_symbol, _number, _string])

application = error('unimplemented -- application')
wlist       = error('unimplemented -- list')
special     = error('unimplemented -- special')

form = alt([symbol, number, string, application, wlist, special])

application.parse = node('application',
                         ('open'     , op               ),
                         ('operator' , cut('form', form)),
                         ('arguments', many0(form)      ),
                         ('close'    , cut(')', cp)     )).parse

wlist.parse = node('list', 
                   ('open'  , os          ), 
                   ('values', many0(form) ),
                   ('close' , cut(']', cs))).parse

special.parse = node('special form',
                     ('open'     , oc                   ),
                     ('operator' , cut('symbol', symbol)),
                     ('arguments', many0(form)          ),
                     ('close'    , cut('}', cc)         )).parse

woof = app(lambda _1, fs, _2: fs, 
           junk,
           many0(form),
           cut('unparsed input remaining', not0(item)))
