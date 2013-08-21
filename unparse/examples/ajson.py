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

# GOAL:  MAKE PARSER LOOK AS SIMILAR TO GRAMMAR AS POSSIBLE
#        INTRODUCE NEW COMBINATORS IF NECESSARY

# still need to check that integers don't have leading 0's (except for the number 0)
# and that the escape sequences from strings are valid
# and that no illegal control characters are in strings

from ..combinators import (bind,    getState,       commit,    run,
                           many0,   app,            optional,  plus,
                           seq2R,   many1,          fmap,      pure,
                           zero,    all_,           any_,      error,
                           seq2L,   itemPosition,   check,     sepBy0,
                           not0,    tokenPosition,  cut,       addError)


item = itemPosition
(literal, satisfy, not1, string) = tokenPosition

def oneOf(cs):
    c_set = set(cs)
    return satisfy(lambda x: x in c_set)

def quantity(p, num):
    return all_([p] * num)

# wish I could put `pairs` in a kwargs dictionary, but then the order would be lost
def node(name, *pairs):
    """
    1. runs parsers in sequence
    2. collects results into a dictionary
    3. grabs state at which parsers started
    4. adds an error frame
    """
    names = map(lambda x: x[0], pairs)
    if len(names) != len(set(names)):
        raise ValueError('duplicate names')
    if '_type' in names:
        raise ValueError('forbidden key: "_type"')
    if '_pos' in names:
        raise ValueError('forbidden key: "_pos"')
    def action(pos, results):
        out = dict(results)
        out['_pos'] = pos
        out['_type'] = name
        return out
    def closure_workaround(s): # captures s
        return lambda y: (s, y)
    return addError(name, 
                    app(action, 
                        getState, 
                        all_([fmap(closure_workaround(s), p) for (s, p) in pairs])))


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

_escape = node('escape', 
               ('open', literal('\\')),
               ('character', item))

_hexC = oneOf('0123456789abcdefABCDEF')

_unic = node('unicode escape',
             ('open', string('\\u')),
             ('escape', cut('expected 4 hexidecimal digits', quantity(_hexC, 4))))

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

array.parse = node('array',
                   ('open', os),
                   ('values', sepBy0(value, comma)),
                   ('close', cut('expected ]', cs))).parse

keyVal = node('key/value pair',
              ('key', jsonstring),
              ('colon', cut('expected :', colon)),
              ('value', cut('expected value', value)))

obj.parse = node('object', 
                 ('open', oc), 
                 ('pairs', sepBy0(keyVal, comma)), 
                 ('close', cut('expected } or ,', cc))).parse

json = node('json',
            ('leading', whitespace), # kind of silly -- the only ws that isn't thrown away
            ('value', plus(obj, array)),
            ('trailing', cut('unparsed input remaining', not0(item)))) # always presents a value of `None` if it succeeds
