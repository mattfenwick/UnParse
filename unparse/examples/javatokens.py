'''
@author: matt
'''
from ..combinators import (many0,  optional,  plus,  app,   pure,
                           seq2R,  many1,     all_,  any_,  error,
                           seq2L,  position,  not0,  Itemizer)
from ..cst import (node, sepBy0, cut)


def quantifier(parser, num):
    return all_([parser] * num)

# problem:  Java allows unicode escapes anywhere, meaning that a single
#   char, from the perspective of the parser, may not correspond to an
#   actual single char in the input stream if there are escapes
# solution: create my own `Itemizer` instance

_raw_hex_digit = position.oneOf('0123456789abcdefABCDEF')
_unicode_escape = app(lambda _1, _2, cs: unichr(int(''.join(cs), 16)),
                      position.literal('\\'),
                      many0(position.literal('u')), # what about a `cut`?
                      quantifier(_raw_hex_digit, 4))

_raw_input_character = plus(_unicode_escape, position.item)

iz = Itemizer(_raw_input_character.parse)

item, oneOf, literal = iz.item, iz.oneOf, iz.literal
satisfy, not1, string = iz.satisfy, iz.not1, iz.string

########### now the real stuff

_line_terminator = any_(map(string, ['\r\n', '\n', '\r']))

_input_character = not1(_line_terminator)

_whitespace = plus(oneOf(' \t\f'), _line_terminator)

_long_comment = node('long comment',
                     ('open', string('/*')),
                     ('body', many0(not1(string('*/')))),
                     ('close', string('*/')))

_short_comment = node('short comment',
                      ('open', string('//')),
                      ('body', many0(_input_character)))

_comment = plus(_long_comment, _short_comment)

FIRST = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_$'
REST = FIRST + '0123456789'

_id_key_null_bool = node('identifier',
                         ('first', oneOf(FIRST)),
                         ('rest', many0(oneOf(REST))))


_decimal_int = node('decimal integer',
                    ('first', oneOf('123456789')),
                    ('rest', many0(oneOf('0123456789_'))))

_hex_int = node('hex int',
                ('zero', literal('0')),
                ('x', oneOf('xX')),
                ('numeral', many1(oneOf('0123456789abcdefABCDEF_'))))

_octal_int = node('octal int',
                  ('zero', literal('0')),
                  ('numeral', many1(oneOf('01234567_'))))

_binary_int = node('binary int', 
                   ('zero', literal('0')),
                   ('b', oneOf('bB')),
                   ('numberal', many1(oneOf('01_'))))

_integer_literal = node('integer',
                        ('numeral', any_([_decimal_int, _hex_int, _octal_int, _binary_int])),
                        ('type suffix', optional(None, oneOf('lL'))))

_digits = node('digits',
               ('first', oneOf('0123456789')),
               ('rest', many0(oneOf('0123456789_'))))

_float_suffix = oneOf('fFdD')

_exponent = node('exponent', 
                 ('e'      , oneOf('eE')),
                 ('sign'   , oneOf('+-')),
                 ('numeral', _digits))

_decimal_fp = ???????????????????????????????????????
DecimalFP:
    Digits  '.'  Digits(?)  Exponent(?)  FloatSuffix(?)
            '.'  Digits     Exponent(?)  FloatSuffix(?)
    Digits                  Exponent     FloatSuffix(?)
    Digits                               FloatSuffix

HexFP:
    '0'  [xX]  HexDigits(?)  '.'     HexDigits  BinaryExponent  FloatSuffix(?)
    '0'  [xX]  HexDigits     '.'(?)             BinaryExponent  FloatSuffix(?)

_binary_exponent = node('binary exponent', 
                        ('p', oneOf('pP')),
                        ('sign', optional(None, oneOf('-+'))),
                        ('numeral', _digits))
BinaryExponent:
    [pP]  [+-](?)  Digits

_fp_literal = plus(_decimal_fp, _hex_fp)

_literal = any_([_integer_literal,
                 _fp_literal,
                 _char_literal,
                 _string_literal])

####################

_some_garbage = '''
Input:
    InputElement(*)  Sub(?)

InputElement:
    WhiteSpace
    Comment
    Token

Token:
    IdentifierOrKeywordOrNullOrBoolean
    Literal
    Separator
    Operator
    '@'
    '...'

Sub:
    the ASCII SUB character, also known as "control-Z"

'''
