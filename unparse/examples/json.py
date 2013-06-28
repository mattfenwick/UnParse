#
# Value   :=  'false'  |  'null'  |  'true'  |  Object  |  Array  |  Number  |  String
# 
# Object  :=  '{'  sepBy0(pair, ',')  '}'
#   where pair  :=  String  ':'  Value
# 
# Array   :=  '['  sepBy0(Value, ',')  ']'
# 
# Number  :=  '-'(?)  body  frac(?)  exponent(?)
#   where body   :=  '0'  |  ( [1-9]  [0-9](*) )
#         frac   :=  '.'  [0-9](+)
#         exponent  :=  [eE]  [-+](?)  [0-9](+)
# 
# String  :=  '"'  ( char  |  escape  |  unicode )(*)  '"'
#   where char    :=  not1( '\\'  |  '"'  |  \u0000-\u001F )
#         escape  :=  '\\'  ["\/bfnrt]                            <-- that's 8 characters
#         unicode :=  '\\u'  [0-9a-eA-E](4)

from .. import combinators as c


item = c.itemPosition
(literal, satisfy, not1, string) = c.tokenPosition

def cut(message, parser):
    return c.bind(c.getState, lambda p: c.commit([(message, p)], parser))

def addError(e, parser):
    return c.bind(c.getState,
                  lambda pos: c.mapError(lambda es: [(e, pos)] + es, parser))
def oneOf(cs):
    return satisfy(lambda x: x in cs)


whitespace = c.many0(oneOf(set(' \t\n\r')))

def numberAction(sign, intp, frac, exp):
    '''
    It's defiitely lazy ... but is it also effective?
    '''
    myString = sign + intp
    if frac == None and exp == None:
        return int(myString)
    if frac is not None:
        myString += '.' + frac
    if exp is not None:
        myString += exp
    return float(myString)

number = c.app(numberAction,
               c.optional('+', literal('-')),
               c.plus(literal('0'), c.app(lambda y, ys: ''.join([y] + ys), oneOf('123456789'), c.many0(oneOf('0123456789')))),
               c.optional(None, c.seq2R(literal('.'), c.fmap(''.join, c.many1(oneOf('0123456789'))))),
               c.optional(None, c.app(lambda x,y,z: ''.join([x,y,''.join(z)]), 
                                      oneOf('eE'), 
                                      c.optional('+', oneOf('+-')),
                                      c.many1(oneOf('0123456789')))))

# is it an error if 0 <= c <= 31 ??
_char = satisfy(lambda x: 32 <= ord(x) and x not in '\\"')

_escapes = {'"': '"',  '\\': '\\', 
            '/': '/',  'b': '\b' ,
            'f': '\f', 'n': '\n' ,
            'r': '\r', 't': '\t'  }

def _escapeAction(x):
    if _escapes.has_key(x):
        return c.pure(_escapes[x])
    return c.zero

_escape = c.seq2R(literal('\\'),
                  c.bind(item, _escapeAction))

_hexC = satisfy(lambda x: x in set('0123456789abcdefABCDEF'))

_unic = c.app(lambda _, cs: unichr(int(''.join(cs), 16)),
             string('\\u'),
             cut('invalid hex escape sequence', c.all_([_hexC] * 4)))

jsonstring = c.app(lambda _1, cs, _2: ''.join(cs),
                   literal('"'),
                   c.many0(c.any_([_char, _escape, _unic])),
                   cut('string: expected "', literal('"')))

boolean = c.plus(c.seq2R(string('true'), c.pure(True)),
                 c.seq2R(string('false'), c.pure(False)))

null = c.seq2R(string('null'), c.pure(None))


obj = c.error('unimplemented')
array = c.error('unimplemented')

def tok(parser):
    return c.seq2L(parser, whitespace)

os, cs, oc, cc, comma, colon = map(lambda x: tok(literal(x)), '[]{},:')

value = c.any_([tok(jsonstring), tok(number), tok(boolean), tok(null), obj, array])



def between(opener, body, closer, message):
    return c.app(lambda _1, bs, _2: bs, 
                 opener,
                 body,
                 cut(message, closer))

def sepBy0(parser, separator):
    return c.optional([], c.app(lambda x, xs: [x] + xs,
                                parser,
                                c.many0(c.seq2R(separator, parser))))


array.parse = addError('array',
                       between(os,
                               sepBy0(value, comma),
                               cs,
                               'expected ]')).parse

keyVal = addError('key/value pair',
                  c.app(lambda k, _, v: (k, v),
                        tok(jsonstring),
                        cut('expected :', colon),
                        cut('expected value', value)))

obj.parse = addError('object',
                     between(oc,
                             sepBy0(keyVal, comma),
                             cc,
                             'expected }')).parse

json = c.app(lambda _1, v, _2: v,
             whitespace, 
             value, # should just be object or array according to RFC 4627
             cut('unparsed input remaining', c.not0(item)))
