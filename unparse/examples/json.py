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

from ..combinators import (many0,   optional,   plus,     node,   app,
                           seq2R,   many1,      all_,     any_,   error,
                           seq2L,   position,   sepBy0,   not0,   cut,    pure)


(item, literal, satisfy) = (position.item, position.literal, position.satisfy)
(oneOf, not1, string) = (position.oneOf, position.not1, position.string)

def quantity(p, num):
    return all_([p] * num)


whitespace = many0(oneOf(' \t\n\r'))

_digits = many1(oneOf('0123456789'))

_decimal = seq2R(literal('.'), 
                 cut('expected digits', _digits))

_exponent = node('exponent', 
                 ('letter', oneOf('eE')), 
                 ('sign', optional('+', oneOf('+-'))),
                 ('power', cut('expected exponent power', _digits)))

_number = node('number', 
               ('integer', plus(_digits, 
                                all_([literal('-'), 
                                      cut('expected digits', _digits)]))),
               ('decimal', optional(None, _decimal)),
               ('exponent', optional(None, _exponent)))

_char = node('character',
             ('value', not1(oneOf('\\"'))))

# yes, this allows *any* character to be escaped
#   invalid characters are handled by a later pass
#   this assumes that doing so will not change the
#   parse result
_escape = node('escape', 
               ('open', literal('\\')),
               ('value', item))

_hexC = oneOf('0123456789abcdefABCDEF')

_unic = node('unicode escape',
             ('open', string('\\u')),
             ('value', cut('expected 4 hexidecimal digits', quantity(_hexC, 4))))

_jsonstring = node('string', 
                   ('open', literal('"')), 
                   ('value', many0(any_([_char, _unic, _escape]))), 
                   ('close', cut('expected "', literal('"'))))

_keyword = node('keyword', 
                ('value', any_(map(string, ['true', 'false', 'null']))))

def tok(parser):
    return seq2L(parser, whitespace)

jsonstring, number, keyword = map(tok, [_jsonstring, _number, _keyword])

os, cs, oc, cc, comma, colon = map(lambda x: tok(literal(x)), '[]{},:')


# a hack to allow mutual recursion of rules
obj = error('unimplemented')
array = error('unimplemented')

value = any_([jsonstring, number, keyword, obj, array])

def sepBy1_(message, p, sep):
    return node('vals',
                ('first', p),
                ('rest', many0(node('pair',
                                    ('sep', sep),
                                    ('value', cut(message, p))))))

def sepBy0_(message, p, sep):
    v2 = seq2R(sep, cut(message, p))
    parser = app(lambda x, ys: [x] + ys,
                 p,
                 many0(v2))
    return plus(parser, pure([]))

array.parse = node('array',
                   ('open', os),
                   ('values', sepBy0_('expected value', value, comma)),
                   ('close', cut('expected ] or ,', cs))).parse

keyVal = node('key/value pair',
              ('key', jsonstring),
              ('colon', cut('expected :', colon)),
              ('value', cut('expected value', value)))

obj.parse = node('object', 
                 ('open', oc), 
                 ('pairs', sepBy0_('expected key/value pair', keyVal, comma)), 
                 ('close', cut('expected } or ,', cc))).parse

_json = node('json',
             ('value', value)) # plus(obj, array)),

json = seq2L(seq2R(whitespace, _json),
             cut('unparsed input remaining', not0(item)))
