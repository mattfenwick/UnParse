# Json    :=  Object  |  Array
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

from ..combinators import (many0,  optional,  app,   pure,
                           seq2R,  many1,     seq,   alt,
                           seq2L,  position,  not0,  error,
                           sepBy0, sepBy1, repeat)
from ..cst import (node, cut)


(item, literal, satisfy) = (position.item, position.literal, position.satisfy)
(oneOf, not1, string) = (position.oneOf, position.not1, position.string)


whitespace = many0(oneOf(' \t\n\r'))

_digits = many1(oneOf('0123456789'))

_decimal = node('decimal',
                ('dot', literal('.')),
                ('digits', cut('digits', _digits)))

_exponent = node('exponent', 
                 ('letter', oneOf('eE')), 
                 ('sign', optional(oneOf('+-'))),
                 ('power', cut('power', _digits)))


_number_1 = node('number', 
                 ('sign', literal('-')),
                 ('integer', cut('digits', _digits)),
                 ('decimal', optional(_decimal)),
                 ('exponent', optional(_exponent)))

_number_2 = node('number', 
                 ('sign', pure(None)), # this is to make the result match the schema of _number_1's result
                 ('integer', _digits),
                 ('decimal', optional(_decimal)),
                 ('exponent', optional(_exponent)))

# there are two number patterns solely to get the error reporting right
#   if there's a `-` but a number can't be parsed, that's an error
_number = alt([_number_1, _number_2])

_char = node('character',
             ('value', not1(oneOf('\\"'))))

# yes, this allows *any* character to be escaped
#   invalid characters are handled by a later pass
#   this assumes that doing so will not change the
#   overall structure of the parse result
_escape = node('escape', 
               ('open', literal('\\')),
               ('value', item))

_hexC = oneOf('0123456789abcdefABCDEF')

_unic = node('unicode escape',
             ('open', string('\\u')),
             ('value', cut('4 hexadecimal digits', repeat(4, _hexC))))

_jsonstring = node('string', 
                   ('open', literal('"')), 
                   ('value', many0(alt([_char, _unic, _escape]))),
                   ('close', cut('double-quote', literal('"'))))

_keyword = node('keyword', 
                ('value', alt(list(map(string, ['true', 'false', 'null'])))))

def tok(parser):
    return seq2L(parser, whitespace)

jsonstring, number, keyword = map(tok, [_jsonstring, _number, _keyword])

os, cs, oc, cc, comma, colon = map(lambda x: tok(literal(x)), '[]{},:')


# a hack to allow mutual recursion of rules
obj = error('unimplemented')
array = error('unimplemented')

value = alt([jsonstring, number, keyword, obj, array])

array.parse = node('array',
                   ('open', os),
                   ('body', sepBy0(value, comma)),
                   ('close', cut('close', cs))).parse

keyVal = node('key/value pair',
              ('key', jsonstring),
              ('colon', cut('colon', colon)),
              ('value', cut('value', value)))

obj.parse = node('object', 
                 ('open', oc), 
                 ('body', sepBy0(keyVal, comma)), 
                 ('close', cut('close', cc))).parse

_json = node('json',
             ('value', value)) # alt(obj, array)),

json = seq2L(seq2R(whitespace, cut('json value', _json)),
             cut('unparsed input remaining', not0(item)))
