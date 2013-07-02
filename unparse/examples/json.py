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

### CST

def Number(p, s, i, d, e):
    return {'type': 'number', 'sign': s,
            'integer': i,     'decimal': e,
            'exponent': e,    'start': p}

def Exponent(s, i):
    return {'type': 'exponent',
            'sign': s, 'integer': i}

def Keyword(p, v):
    return {'start': p, 'type': 'keyword',
            'value': v}

def String(p, cs, s):
    return {'type': 'string', 'start': p,
            'chars': cs,      'stop' : s}

def Object(p, pairs, s):
    return {'type': 'object', 'start': p,
            'pairs': pairs,   'stop': s}
    
def Array(p, elems, s):
    return {'type': 'array', 'start': p,
            'elems': elems,  'stop': s}

###

item = itemPosition
(literal, satisfy, not1, string) = tokenPosition

def cut(message, parser):
    return bind(getState, lambda p: commit([(message, p)], parser))

def addError(e, parser):
    return bind(getState,
                lambda pos: mapError(lambda es: [(e, pos)] + es, parser))
def oneOf(cs):
    return satisfy(lambda x: x in cs)


number = app(Number,
             getState,
             optional('+', literal('-')),
             plus(literal('0'), app(lambda y, ys: ''.join([y] + ys), oneOf('123456789'), many0(oneOf('0123456789')))),
             optional(None, seq2R(literal('.'), fmap(''.join, many1(oneOf('0123456789'))))),
             optional(None, app(lambda _,y,z: Exponent(y, z), 
                                oneOf('eE'), 
                                optional('+', oneOf('+-')),
                                fmap(''.join, many1(oneOf('0123456789'))))))

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
                      app(String,
                          seq2L(getState, literal('"')),
                          fmap(''.join, many0(any_([_char, _unic, _escape]))),
                          seq2L(getState, cut('expected "', literal('"')))))

keyword = app(Keyword,
              getState,
              any_(map(string, ['true', 'false', 'null'])))


# hack to allow mutual recursion of rules
obj = error('unimplemented')
array = error('unimplemented')

whitespace = many0(oneOf(set(' \t\n\r')))

def tok(parser):
    return seq2L(parser, whitespace)

os, cs, oc, cc, comma, colon = map(lambda x: seq2L(getState, tok(literal(x))), '[]{},:')

value = any_([tok(jsonstring), tok(number), tok(keyword), obj, array])



def sepBy0(parser, separator):
    return optional([], app(lambda x, xs: [x] + xs,
                            parser,
                            many0(seq2R(separator, parser))))


array.parse = addError('array',
                       app(Array,
                           os,
                           sepBy0(value, comma),
                           cut('expected ]', cs))).parse

keyVal = addError('key/value pair',
                  app(lambda k, _, v: (k, v),
                      tok(jsonstring),
                      cut('expected :', colon),
                      cut('expected value', value)))

obj.parse = addError('object',
                     app(Object,
                         oc,
                         sepBy0(keyVal, comma),
                         cut('expected }', cc))).parse

json = app(lambda _1, v, _2: v,
           whitespace, 
           plus(obj, array),
           cut('unparsed input remaining', not0(item)))
