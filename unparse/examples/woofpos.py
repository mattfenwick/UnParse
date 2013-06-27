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
#   - position tracking (line/column)
#   - error reporting -- stack of errors

from .. import combinators as c


item = c.itemPosition
(literal, satisfy, not1, _) = c.tokenPosition


comment = c.seq2R(literal(';'), c.many0(not1(literal('\n'))))

WHITESPACE = set(' \t\n\r\f')
whitespace = satisfy(lambda x: x in WHITESPACE)

junk = c.many0(c.plus(comment, whitespace))

DIGITS = set('0123456789')
number = c.fmap(lambda ds: int(''.join(ds)), c.many1(satisfy(lambda x: x in DIGITS)))

SYMBOLSTART = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
symbol = c.app(lambda x, y: ''.join([x] + y),
                    satisfy(lambda x: x in SYMBOLSTART),
                    c.many0(satisfy(lambda x: x in SYMBOLSTART.union(DIGITS))))


op = literal('(')
cp = literal(')')
os = literal('[')
cs = literal(']')
oc = literal('{')
cc = literal('}')


def tok(parser):
    return c.seq2L(parser, junk)

def cut(message, parser):
    return c.bind(c.getState, lambda p: c.commit([(message, p)], parser))

def addError(e, parser):
    return c.bind(c.getState,
                  lambda pos: c.mapError(lambda es: [(e, pos)] + es, parser))


app = c.error('unimplemented -- app')
wlist = c.error('unimplemented -- list')
special = c.error('unimplemented -- special')

form = c.any_([tok(symbol), tok(number), app, wlist, special])


def between(opener, body, closer, message):
    return c.app(lambda _1, bs, _2: bs, 
                 opener,
                 c.many0(c.plus(body, c.seq2L(not1(closer), cut('delimited: invalid content', c.zero)))),
                 cut(message, closer))
    
app.parse = addError('application',
                     between(tok(op), 
                             form, 
                             tok(cp),
                             'missing )')).parse

wlist.parse = addError('list', 
                       between(tok(os),
                               form,
                               tok(cs),
                               'missing ]')).parse

special.parse = addError('special form',
                         between(tok(oc),
                                 form, 
                                 tok(cc),
                                 'missing }')).parse

end = c.not0(item)

woof = c.app(lambda _1, fs, _2: fs, 
             junk,
             c.many0(form),
             cut('woof: unparsed input remaining', end))
