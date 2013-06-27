#
# Value   :=  'false'  |  'null'  |  'true'  |  Object  |  Array  |  Number  |  String
# 
# Object  :=  '{'  sepBy0(',', String  ':'  Value )  '}'
# 
# Array   :=  '['  sepBy0(',', Value)  ']'
# 
# Number  :=  '-'(?)  ( '0'  |  ( [1-9]  
# 
# 
# 
# 

from .. import combinators as c


item = c.itemPosition
(literal, satisfy, not1, _) = c.tokenPosition

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


def between(opener, body, closer, message):
    return c.app(lambda _1, bs, _2: bs, 
                 opener,
                 c.many0(c.plus(body, c.seq2L(not1(closer), cut('delimited: invalid content', c.zero)))),
                 cut(message, closer))

