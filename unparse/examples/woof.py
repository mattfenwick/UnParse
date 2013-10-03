#
# Woof  :=  Form(*)
#
# Form  :=  App     |  Special  |  List    |  
#           Symbol  |  Number   |  String
#
# App   :=  '('  Form(+)  ')'
#
# Special  :=  '{'  Form(*)  '}'
#
# List  :=  '['  Form(*)  ']'
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

from .. import combinators as c


position = c.position
(item, literal, satisfy) = (position.item, position.literal, position.satisfy)
(oneOf, not1, string) = (position.oneOf, position.not1, position.string)


comment = c.seq2R(literal(';'), c.many0(not1(literal('\n'))))

WHITESPACE = ' \t\n\r\f'
whitespace = c.many0(c.oneOf(WHITESPACE))

junk = c.plus(comment, whitespace)

def tok(p):
    return c.seq2L(p, c.many0(junk))


DIGITS = '0123456789'
number = c.many1(c.oneOf(DIGITS))

SYMBOLSTART = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
symbol = c.app(lambda x, y: [x] + y,
                    c.oneOf(SYMBOLSTART),
                    c.many0(c.oneOf(SYMBOLSTART + DIGITS)))

op = literal('(')
cp = literal(')')
os = literal('[')
cs = literal(']')
oc = literal('{')
cc = literal('}')


app = c.error('unimplemented -- app')
wlist = c.error('unimplemented -- list')
special = c.error('unimplemented -- special')

form = c.any_([tok(symbol), tok(number), app, wlist, special])

app.parse = c.app(lambda _1, b, _2: b,
                  tok(op),
                  c.many1(form),
                  tok(cp)).parse

wlist.parse = c.app(lambda _1, b, _2: b,
                    tok(os),
                    c.many0(form),
                    tok(cs)).parse

special.parse = c.app(lambda _1, b, _2: b,
                      tok(oc),
                      c.many0(form),
                      tok(cc)).parse
