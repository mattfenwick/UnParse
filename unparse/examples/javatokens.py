'''
@author: matt
'''
from ..combinators import (many0,  optional,  app,   pure, repeat,
                           seq2R,  many1,     seq,   alt,   error,
                           seq2L,  position,  not0,  Itemizer, position)
from ..cst import (node, cut)


# problem:  Java allows unicode escapes anywhere, meaning that a single
#   char, from the perspective of the parser, may not correspond to an
#   actual single char in the input stream if there are escapes
# solution: create my own `Itemizer` instance
# TODO fix this up somehow.  for now, just ignore
#_raw_hex_digit = position.oneOf('0123456789abcdefABCDEF')
#_unicode_escape = app(lambda _1, _2, cs: unichr(int(''.join(cs), 16)),
#                      position.literal('\\'),
#                      many0(position.literal('u')), # what about a `cut`?
#                      repeat(4, _raw_hex_digit))
#
#_raw_input_character = alt([_unicode_escape, position.item])
#
#iz = Itemizer(_raw_input_character.parse)
iz = position

item, oneOf, literal = iz.item, iz.oneOf, iz.literal
satisfy, not1, string = iz.satisfy, iz.not1, iz.string

########### now the real stuff

_line_terminator = alt(list(map(string, ['\r\n', '\n', '\r'])))

_input_character = not1(_line_terminator)

_whitespace = alt([oneOf(' \t\f'), _line_terminator])

_long_comment = node('long comment',
                     ('open', string('/*')),
                     ('body', many0(not1(string('*/')))),
                     ('close', string('*/')))

_short_comment = node('short comment',
                      ('open', string('//')),
                      ('body', many0(_input_character)))

_comment = alt([_long_comment, _short_comment])

FIRST = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_$'
REST = FIRST + '0123456789'

_identifier = node('identifier',
                   ('first', oneOf(FIRST)),
                   ('rest', many0(oneOf(REST))))


_digits = node('digits',
               ('first', oneOf('0123456789')),
               ('rest', many0(oneOf('0123456789_'))))

_exponent = node('exponent', 
                 ('e'      , oneOf('eE')),
                 ('sign'   , optional(oneOf('+-'))),
                 ('numeral', _digits))

_num_8_10 = node('int8/10',
                 ('integer' , _digits),
                 ('dot'     , optional(literal('.'))),
                 ('decimal' , optional(_digits)),
                 ('exponent', optional(_exponent)))

_num_8_10_dot = node('int8/10',
                     ('integer' , pure(None)),
                     ('dot'     , literal('.')),
                     ('decimal' , _digits),
                     ('exponent', optional(_exponent)))

_hex_digit = oneOf('0123456789abcdefABCDEF_')

_binary_exponent = node('binary exponent', 
                        ('p'      , oneOf('pP')),
                        ('sign'   , optional(oneOf('-+'))),
                        ('numeral', _digits))
_num_16 = node('int16',
               ('zero'    , literal('0')),
               ('x'       , oneOf('xX')),
               ('integer' , many0(_hex_digit)),
               ('dot'     , optional(literal('.'))),
               ('decimal' , many0(_hex_digit)),
               ('exponent', _binary_exponent))

_num_2 = node('int2', 
              ('zero', literal('0')),
              ('b', oneOf('bB')),
              ('numeral', many1(oneOf('01_'))))

_num_literal = node('number',
                    ('numeral', alt([_num_2, _num_16, _num_8_10, _num_8_10_dot])),
                    ('type'   , optional(oneOf('fFdDlL'))))

_single = not1(oneOf("'\\"))

_escape = node('escape',
               ('open', literal('\\')),
               ('value', oneOf('btnfr"\'\\')))

_octal_escape = node('octal escape',
                     ('open', literal('\\')),
                     ('value', alt([seq([oneOf('0123'), oneOf('01234567'), oneOf('01234567')]),
                                   seq([oneOf('01234567'), optional(oneOf('01234567'))])])))

_char_literal = node('char',
                     ('open', literal("'")),
                     ('value', alt([_single, _escape, _octal_escape])),
                     ('close', literal("'")))

_string_literal = node('string',
                       ('open', literal('"')),
                       ('value', many0(alt([_single, _escape, _octal_escape]))),
                       ('close', literal('"')))

_literal = alt([_num_literal,
                _char_literal,
                _string_literal])

SEPARATORS = ['(', ')', '{', '}', '[', ']', ';', ',', '.']

OPERATORS = [
    '='  , '>'  , '<' , '!' , '~'  , '?' , ':'  ,
    '==' , '<=' , '>=', '!=', '&&' , '||', '++' ,
    '--' , '+'  , '-' , '*' , '/'  , '&' , '|'  ,
    '^'  , '%'  , '<<', '>>', '>>>', '+=', '-=' ,
    '*=' , '/=' , '&=', '|=', '^=' , '%=', '<<=',
    '>>=', '>>>=']

OTHERS = ['...', '@']

# what about position of _other, _separator, and _operator?
_other = alt(list(map(string, OTHERS)))

_separator = alt(list(map(literal, SEPARATORS)))

_operator = alt(list(map(string, OPERATORS)))

# are these in the right order?  i.e. `...` needs to be before `.`
_token = alt([_identifier, _literal, _other, _separator, _operator])

_input_element = alt([_whitespace, _comment, _token])

# can't use name `input` -- it's a built-in python function
tokenizer = many0(_input_element) # what about the optional trailing `Sub`?
