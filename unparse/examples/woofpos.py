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
from ..conslist import ConsList


def parsers(item):
    mySatisfy = item.check
    def myLiteral(t):
        return mySatisfy(lambda x: x == t)
    def myNot1(p):
        return p.not0().seq2R(item)
    return (mySatisfy, myLiteral, myNot1)


def bump(x):
    def action(y): # what's this syntax called:  def x((a, b)): ... ????
        line, col = y
        if x == '\n':
            return (line + 1, 1)
        return (line, col + 1)
    return Parser.updateState(action).seq2R(Parser.pure(x))

item = Parser.item.bind(bump)

satisfy, literal, not1 = parsers(item)

# another issue caused by this problem of needing to redefine the basic item
#   parser:  not1 has changed from a method call to a "free" function
comment = literal(';').seq2R(not1(literal('\n')).many0())

WHITESPACE = set(' \t\n\r\f')
whitespace = satisfy(lambda x: x in WHITESPACE)

junk = comment.plus(whitespace).many0()

def tok(p):
    return p.seq2L(junk)

DIGITS = set('0123456789')
number = satisfy(lambda x: x in DIGITS).many1().fmap(lambda ds: int(''.join(ds)))

SYMBOLSTART = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
symbol = Parser.app(lambda x, y: ''.join([x] + y),
                    satisfy(lambda x: x in SYMBOLSTART),
                    satisfy(lambda x: x in SYMBOLSTART.union(DIGITS)).many0())

op = literal('(')
cp = literal(')')
os = literal('[')
cs = literal(']')
oc = literal('{')
cc = literal('}')

def cut(message, parser):
    return Parser.getState.bind(lambda p: parser.commit((message, p)))

app = Parser.error('unimplemented -- app')
wlist = Parser.error('unimplemented -- list')
special = Parser.error('unimplemented -- special')

form = Parser.any([tok(symbol), tok(number), app, wlist, special])

app.parse = Parser.app(lambda _1, op, args, _2: (op, args),
                       tok(op),
                       cut('application: missing operator', form),
                       form.many0(),
                       cut('application: missing )', tok(cp))).parse

wlist.parse = Parser.app(lambda _1, vs, _2: vs,
                         tok(os),
                         form.many0(),
                         cut('list: missing ]', tok(cs))).parse

special.parse = Parser.app(lambda _1, fs, _2: fs,
                           tok(oc),
                           form.many0(),
                           cut('special form: missing }', tok(cc))).parse

end = item.not0()

woof = junk.seq2R(form.many0()).seq2L(cut('woof: unparsed input remaining', end))


def parse(parser, inp):
    return parser.parse(ConsList(inp, 0), (1, 1))
