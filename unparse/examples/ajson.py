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
            ('value', value), # plus(obj, array)),
            ('trailing', cut('unparsed input remaining', not0(item)))) # always presents a value of `None` if it succeeds


# tree traversal
#
# checks:
#
# maps:
#
# doneskies:
#    integers don't have leading 0's (except for the number 0)
#    no number overflow
#    no duplicate keys in maps
#    number literals to numbers
#    no illegal control characters are in strings
#    escape sequences from strings are valid
#    unicode escape sequences to chars
#    characters to chars
#    escapes to chars
#    join up string literal

from ..maybeerror import MaybeError as Me

def add_error(message, position, comp):
    return comp.mapError(lambda es: [(message, position)] + es)

_escapes = {'"': '"',  '\\': '\\', 
            '/': '/',  'b': '\b' ,
            'f': '\f', 'n': '\n' ,
            'r': '\r', 't': '\t'  }

def t_char(node):
    val = node['value']
    if node['_type'] == 'unicode escape':
        return Me.pure(unichr(int(''.join(val), 16)))
    elif node['_type'] == 'escape':
        # is the escape sequence valid?
        if val in _escapes:
            return Me.pure(_escapes[val])
        return Me.error([('invalid escape sequence', node['_pos'])])
    elif node['_type'] == 'character':
        # no control characters allowed!
        if ord(val) < 32:
            return Me.error([('invalid control character', node['_pos'])])
        return Me.pure(val)
    raise TypeError('invalid character node type -- ' + str(node['_type']))

def t_string(node):
    # check that node _type is string (optional)
    # pull out the value (?), fix up all the characters, join them into a string
    # watch out for errors, reporting position if necessary
    return add_error('string', node['_pos'], Me.app(lambda *args: ''.join(args), *map(t_char, node['value'])))

def t_number(node):
    # check that node _type is number (optional)
    i = ''.join(node['integer'])
    # check that there's no leading 0's
    if i[0] == '0' and len(i) > 1:
        return Me.error([('invalid leading 0 in number', node['_pos'])])
    d = ''.join(node['decimal']) if node['decimal'] else ''
    exp = ''
    if node['exponent']:
        exp += node['exponent']['letter']
        exp += node['exponent']['sign']
        exp += ''.join(node['exponent']['power'])
    val = ''.join([i, '.', d, exp])
    # convert to a float
    num = float(val)
    # check for overflow
    if num in map(float, ['inf', '-inf']):
        return Me.error([('floating-point overflow', node['_pos'])])
    return Me.pure(num)

_keywords = {
    'true': True,
    'false': False,
    'null': None
}

def t_keyword(node):
    if node['value'] in _keywords:
        return Me.pure(_keywords[node['value']])
    return Me.error([('invalid keyword', node['_pos'])])

def t_array(node):
    return add_error('array', node['_pos'], Me.app(lambda *args: list(args), *map(t_value, node['values'])))

def t_pair(node):
    return add_error('key/value pair', node['_pos'], 
                     Me.app(lambda *args: args, t_string(node['key']), t_value(node['value']), Me.pure(node['_pos'])))

def t_build_object(pairs):
    obj = {}
    pos = {}
    for (k, v, p) in pairs:
        if obj.has_key(k):
            return Me.error([('first key usage', pos[k]), ('duplicate key', p)])
        obj[k] = v
        pos[k] = p
    return Me.pure(obj)

def t_object(node):
    # this is really silly.  it should be something like a fold instead
    return add_error('object', node['_pos'],
                     Me.app(lambda *args: list(args), *map(t_pair, node['pairs'])).bind(t_build_object))

_values = {
    'keyword': t_keyword,
    'number': t_number,
    'string': t_string,
    'array': t_array,
    'object': t_object
}

def t_value(node):
    return _values[node['_type']](node)

def t_json(node):
    return t_value(node['value'])

def full(x):
    return run(json, x).bind(lambda r: t_json(r['result']))
