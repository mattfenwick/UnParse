# tree traversal
#
# checks:
#
# maps:
#
# doneskies:
#    integer portion of number: no leading 0's (except for the number 0)
#    no number overflow
#    no duplicate keys in maps
#    number literals to numbers
#    no illegal control characters are in strings
#    escape sequences from strings are valid
#    unicode escape sequences to chars
#    characters to chars
#    escapes to chars
#    join up string literal

#from __future__ import print_function
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
    if node['_name'] == 'unicode escape':
        return Me.pure(chr(int(''.join(val), 16)))
    elif node['_name'] == 'escape':
        # is the escape sequence valid?
        if val in _escapes:
            return Me.pure(_escapes[val])
        return Me.error([('invalid escape sequence', node['_start'])])
    elif node['_name'] == 'character':
        # no control characters allowed!
        if ord(val) < 32:
            return Me.error([('invalid control character', node['_start'])])
        return Me.pure(val)
    raise TypeError('invalid character node type -- ' + str(node['_name']))

def t_string(node):
    # check that node _name is string (optional)
    # pull out the value (?), fix up all the characters, join them into a string
    # watch out for errors, reporting position if necessary
    return add_error('string', node['_start'], Me.app(lambda *args: ''.join(args), *list(map(t_char, node['value']))))

def t_number(node):
    # check that node _name is number (optional)
    sign = node['sign'] if node['sign'] else '+'
    i = ''.join(node['integer'])
    # check that there's no leading 0's
    if i[0] == '0' and len(i) > 1:
        return Me.error([('number: invalid leading 0', node['_start'])])
    d = ''.join(node['decimal']['digits']) if node['decimal'] else ''
    exp = ''
    if node['exponent']:
        exp += node['exponent']['letter']
        if node['exponent']['sign']:
            exp += node['exponent']['sign']
        exp += ''.join(node['exponent']['power'])
    val = ''.join([sign, i, '.', d, exp])
#    print(val, node)
    # convert to a float
    num = float(val)
    # check for overflow
    if num in map(float, ['inf', '-inf']):
        return Me.error([('number: floating-point overflow', node['_start'])])
    return Me.pure(num)

_keywords = {
    'true': True,
    'false': False,
    'null': None
}

def t_keyword(node):
    if node['value'] in _keywords:
        return Me.pure(_keywords[node['value']])
    return Me.error([('invalid keyword', node['_start'])])

def t_array(node):
#    print('node: ', node)
    return add_error('array', 
                     node['_start'], 
                     Me.app(lambda *args: list(args), # this may look super weird -- but it's for the error effects
                            *list(map(t_value, [] if node['body'] is None else [node['body'][0]] + [b for (_, b) in node['body'][1]]))))

def t_pair(node):
    return add_error('key/value pair', 
                     node['_start'], 
                     Me.app(lambda *args: args, 
                            t_string(node['key']), 
                            t_value(node['value']), 
                            Me.pure(node['_start'])))

def t_build_object(pairs):
    obj = {}
    pos = {}
    for (k, v, p) in pairs:
        if k in obj:
            return Me.error([('first key usage', pos[k]), ('duplicate key', p)])
        obj[k] = v
        pos[k] = p
    return Me.pure(obj)

def t_object(node):
    # this is really silly.  it should be something like a fold instead
    return add_error('object', 
                     node['_start'],
                     Me.app(lambda *args: list(args), 
                            *list(map(t_pair, [node['body'][0]] + [b for (_, b) in node['body'][1]]))).bind(t_build_object))

_values = {
    'keyword': t_keyword,
    'number' : t_number ,
    'string' : t_string ,
    'array'  : t_array  ,
    'object' : t_object
}

def t_value(node):
    return _values[node['_name']](node)

def t_json(node):
    return t_value(node['value'])

def full(input_string):
    """
    run parser over input, building CST, then 
    run a tree traversal over CST, checking for
    other kinds of errors
    """
    cst = run(json, input_string)
    return cst.bind(lambda r: t_json(r['result']))
