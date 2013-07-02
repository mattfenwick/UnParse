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

from ..combinators import (bind,   getState, commit,   mapError,
                           many0,  app,      optional, plus,
                           seq2R,  many1,    fmap,     pure,
                           zero,   all_,     any_,     error,
                           seq2L,  itemPosition, tokenPosition,
                           not0)


item = itemPosition
(literal, satisfy, not1, string) = tokenPosition

def cut(message, parser):
    return bind(getState, lambda p: commit([(message, p)], parser))

def addError(e, parser):
    return bind(getState,
                lambda pos: mapError(lambda es: [(e, pos)] + es, parser))
def oneOf(cs):
    return satisfy(lambda x: x in cs)


whitespace = many0(oneOf(set(' \t\n\r')))

def numberAction(sign, intp, frac, exp):
    '''
    It's definitely lazy ... but is it also effective?
    '''
    myString = sign + intp
    if frac == None and exp == None:
        return int(myString)
    if frac is not None:
        myString += '.' + frac
    if exp is not None:
        myString += exp
    return float(myString)

number = app(numberAction,
             optional('+', literal('-')),
             plus(literal('0'), app(lambda y, ys: ''.join([y] + ys), oneOf('123456789'), many0(oneOf('0123456789')))),
             optional(None, seq2R(literal('.'), fmap(''.join, many1(oneOf('0123456789'))))),
             optional(None, app(lambda x,y,z: ''.join([x,y,''.join(z)]), 
                                oneOf('eE'), 
                                optional('+', oneOf('+-')),
                                many1(oneOf('0123456789')))))

# is it an error if 0 <= c <= 31 ??
#_char = satisfy(lambda x: 32 <= ord(x) and x not in '\\"')
def _charCheck(c):
    if c in '\\"':
        return zero
    elif ord(c) < 32:
        return error([])
    return pure(c)
_char = addError('illegal control character', bind(item, _charCheck))

_escapes = {'"': '"',  '\\': '\\', 
            '/': '/',  'b': '\b' ,
            'f': '\f', 'n': '\n' ,
            'r': '\r', 't': '\t'  }

def _escapeAction(x):
    if _escapes.has_key(x):
        return pure(_escapes[x])
    return zero

_escape = seq2R(literal('\\'),
                cut('illegal escape', bind(item, _escapeAction)))

_hexC = satisfy(lambda x: x in set('0123456789abcdefABCDEF'))

_unic = app(lambda _, cs: unichr(int(''.join(cs), 16)),
           string('\\u'),
           cut('invalid hex escape sequence', all_([_hexC] * 4)))

jsonstring = addError('string',
                      app(lambda _1, cs, _2: ''.join(cs),
                          literal('"'),
                          many0(any_([_char, _unic, _escape])),
                          cut('expected "', literal('"'))))

boolean = plus(seq2R(string('true'), pure(True)),
               seq2R(string('false'), pure(False)))

null = seq2R(string('null'), pure(None))


# hack to allow mutual recursion of rules
obj = error('unimplemented')
array = error('unimplemented')

def tok(parser):
    return seq2L(parser, whitespace)

os, cs, oc, cc, comma, colon = map(lambda x: tok(literal(x)), '[]{},:')

value = any_([tok(jsonstring), tok(number), tok(boolean), tok(null), obj, array])



def sepBy0(parser, separator):
    return optional([], app(lambda x, xs: [x] + xs,
                            parser,
                            many0(seq2R(separator, parser))))


array.parse = addError('array',
                       app(lambda _1, bs, _2: bs,
                           os,
                           sepBy0(value, comma),
                           cut('expected ]', cs))).parse

keyVal = addError('key/value pair',
                  app(lambda k, _, v: (k, v),
                      tok(jsonstring),
                      cut('expected :', colon),
                      cut('expected value', value)))

obj.parse = addError('object',
                     app(lambda _1, bs, _2: bs,
                         oc,
                         sepBy0(keyVal, comma),
                         cut('expected }', cc))).parse

json = app(lambda _1, v, _2: v,
           whitespace, 
           plus(obj, array),
           cut('unparsed input remaining', not0(item)))
