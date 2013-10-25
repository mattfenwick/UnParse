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
from .json import json
from ..combinators import run

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
    print 'node: ', node
    return add_error('array', 
                     node['_pos'], 
                     Me.app(lambda *args: list(args), # this may look super weird -- but it's for the error effects
                            *map(t_value, node['body']['values'])))

def t_pair(node):
    return add_error('key/value pair', 
                     node['_pos'], 
                     Me.app(lambda *args: args, 
                            t_string(node['key']), 
                            t_value(node['value']), 
                            Me.pure(node['_pos'])))

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
    return add_error('object', 
                     node['_pos'],
                     Me.app(lambda *args: list(args), 
                            *map(t_pair, node['body']['values'])).bind(t_build_object))

_values = {
    'keyword': t_keyword,
    'number' : t_number ,
    'string' : t_string ,
    'array'  : t_array  ,
    'object' : t_object
}

def t_value(node):
    return _values[node['_type']](node)

def t_json(node):
    return t_value(node['value'])

def full(input_string):
    """
    run parser over input, building CST, then 
    run a tree traversal over CST, checking for
    other kinds of errors
    """
    cst = run(json, input_string)
    print cst
    return cst.bind(lambda r: t_json(r['result']))
