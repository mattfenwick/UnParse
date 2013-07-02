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

def buildNumber(sign, intp, frac, exp):
    # integer portion starts with 2+ 0s -- not okay
    # all other non-empty integer portions -- okay
    if intp[:2] == '00':
        return cut('leading 0', zero)
        
    myString = sign + intp
    if frac == None and exp == None:
        return pure(int(myString))
    
    if frac is not None:
        myString += '.' + frac
    if exp is not None:
        myString += exp
    f = float(myString)
    if f in [float('inf'), float('-inf')]:
        return cut('floating-point overflow', zero)
    return pure(f)

_digits = fmap(''.join, many1(oneOf('0123456789')))
_decimal = seq2R(literal('.'), 
                 cut('expected digits', _digits))
_exponent = app(lambda *xs: ''.join(xs),
                oneOf('eE'), 
                optional('+', oneOf('+-')),
                cut('expected exponent', _digits))

_number = bind(all_([optional('+', literal('-')),
                     _digits,
                     optional(None, _decimal),
                     optional(None, _exponent)]),
               lambda xs: buildNumber(*xs))

number = addError('number', _number)

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

keyword = any_([seq2R(string(s), pure(v)) for (s, v) in [('true', True), ('false', False), ('null', None)]])


# hack to allow mutual recursion of rules
obj = error('unimplemented')
array = error('unimplemented')

def tok(parser):
    return seq2L(parser, whitespace)

os, cs, oc, cc, comma, colon = map(lambda x: tok(literal(x)), '[]{},:')

value = any_([tok(jsonstring), tok(number), tok(keyword), obj, array])



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
                  app(lambda p, k, _, v: (p, k, v),
                      getState,
                      tok(jsonstring),
                      cut('expected :', colon),
                      cut('expected value', value)))

def buildObject(pairs):
    obj = {}
    for (p, k, v) in pairs:
        if obj.has_key(k):
            return error([('duplicate key: ' + k, p)])
        obj[k] = v
    return pure(obj)

obj.parse = addError('object',
                     app(lambda _1, bs, _2: bs,
                         oc,
                         bind(sepBy0(keyVal, comma), buildObject),
                         cut('expected }', cc))).parse

json = app(lambda _1, v, _2: v,
           whitespace, 
           plus(obj, array),
           cut('unparsed input remaining', not0(item)))
