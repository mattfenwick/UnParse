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

from ..standard import Parser


comment = Parser.literal(';').seq2R(Parser.literal('\n').not1().many0())

WHITESPACE = set(' \t\n\r\f')
whitespace = Parser.satisfy(lambda x: x in WHITESPACE)

junk = comment.plus(whitespace)

def tok(p):
    return p.seq2L(junk.many0())

DIGITS = set('0123456789')
number = Parser.satisfy(lambda x: x in DIGITS).many1()

SYMBOLSTART = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
symbol = Parser.app(lambda x, y: [x] + y,
                    Parser.satisfy(lambda x: x in SYMBOLSTART),
                    Parser.satisfy(lambda x: x in SYMBOLSTART.union(DIGITS)).many0())

op = Parser.literal('(')
cp = Parser.literal(')')
os = Parser.literal('[')
cs = Parser.literal(']')
oc = Parser.literal('{')
cc = Parser.literal('}')


app = Parser.error('unimplemented -- app')
wlist = Parser.error('unimplemented -- list')
special = Parser.error('unimplemented -- special')

form = Parser.any([tok(symbol), tok(number), app, wlist, special])

app.parse = tok(op).seq2R(form.many1()).seq2L(tok(cp)).parse

wlist.parse = tok(os).seq2R(form.many0()).seq2L(tok(cs)).parse

special.parse = tok(oc).seq2R(form.many0()).seq2L(tok(cc)).parse
