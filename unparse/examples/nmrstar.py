'''
@author: matt
'''
from .. import combinators as c
from .. import conslist
from . import concrete


item = c.itemPosition
(literal, satisfy, not1, _) = c.tokenPosition


extract = ''.join

def oneOf(cs):
    return satisfy(lambda x: x in cs)

def cut(message, parser):
    return c.bind(c.getState, lambda p: c.commit(parser, (message, p)))


NEWLINES, BLANKS = set('\n\r'), set(' \t')
SPACES = NEWLINES.union(BLANKS)
SPECIALS = SPACES.union(set('"#\'_')) # double-quote, pound, single-quote, underscore

newline, blank, space, special = map(oneOf, [NEWLINES, BLANKS, SPACES, SPECIALS])

_identifier  =  c.app(lambda pos, _, bs: concrete.Key(pos, extract(bs)), 
                      c.getState, 
                      literal('_'), 
                      c.many1(not1(space)))


sc, sq, dq = map(literal, ';\'"')

end = c.not0(item)
_notSpaceOrEnd = c.not0(c.plus(space, end))
nonEndingSq = c.seq2L(sq, _notSpaceOrEnd)
nonEndingDq = c.seq2L(dq, _notSpaceOrEnd)

# empty        ->  fail
# not newline  ->  fail
# newline      ->  error
# (no success)
_newlineErr = c.seq2L(newline, cut('illegal newline in quoted string', c.zero))

sqstring = c.app(lambda pos, _1, cs, _2: concrete.Value(pos, extract(cs)),
                 c.getState,
                 sq, 
                 c.many0(c.plus(nonEndingSq, not1(c.plus(sq, _newlineErr)))),
                 cut('unclosed single-quoted string', sq))

dqstring = c.app(lambda pos, _1, cs, _2: concrete.Value(pos, extract(cs)),
                 c.getState,
                 dq, 
                 c.many0(c.plus(nonEndingDq, not1(c.plus(dq, _newlineErr)))),
                 cut('unclosed double-quoted string', dq))

_quotedvalue = c.plus(sqstring, dqstring)


comment = c.app(lambda pos, _, b: concrete.Comment(pos, extract(b)), 
                c.getState,
                literal('#'),
                c.many0(not1(newline))) 

whitespace = c.app(concrete.Whitespace,
                   c.getState,
                   c.fmap(extract, c.many1(c.plus(blank, newline))))

junk = c.many0(c.plus(whitespace, comment))


endsc = c.seq2R(newline, sc)

def scRest(ws):
    if len(ws) == 0:
        return c.zero # could this even happen? no because we made sure it matched at least 1
    # a semicolon-delimited string must be preceded by a newline
    elif isinstance(ws[-1], concrete.Whitespace) and ws[-1].string[-1] in NEWLINES:
        return c.app(lambda pos, _1, b, _2: concrete.Value(pos, extract(b)),
                     c.getState, # oh ... all other uses of getState might'nt work because we're pre-munching ... have to check
                     sc,
                     c.many0(not1(endsc)),
                     cut('unclosed semicolon-delimited string', endsc))
    else:
        return c.zero
    
scstring = c.bind(c.many1(c.plus(whitespace, comment)), scRest)

def classify(meta, theString): # 'theString' in order to avoid shadowing
    '''
    Classifications:
     - reserved: /stop_/, /loop_/, /save_.*/, /data_.+/
     - value:  everything else
    '''
    Reserved = concrete.Reserved
    if theString.lower() == "stop_":
        return Reserved(meta, "stop", '')
    elif theString[:5].lower() == "save_":
        if len(theString) != 5:
            return Reserved(meta, "saveopen", theString[5:])
        return Reserved(meta, "saveclose", '')
    elif theString.lower() == "loop_":
        return Reserved(meta, "loop", '')
    elif theString[:5].lower() == "data_" and len(theString) > 5:
        return Reserved(meta, "dataopen", theString[5:])
    return concrete.Value(meta, theString)

_uqvalue_or_keyword = c.app(lambda pos, c1, cs: classify(pos, extract([c1] + cs)),
                            c.getState,
                            not1(special),
                            c.many0(not1(space)))


def munch(parser):
    return c.seq2R(junk, parser)

uqvalue_or_keyword = munch(_uqvalue_or_keyword)

identifier  =  munch(_identifier)
value   =  c.check(lambda val: isinstance(val, concrete.Value), 
                   c.any_([munch(_quotedvalue), scstring, uqvalue_or_keyword]))


# syntactic combinations
#   data blocks, save frames, loops, key/value pairs

def keyword(rtype):
    return c.check(lambda val: isinstance(val, concrete.Reserved) and val.rtype == rtype, 
                   uqvalue_or_keyword)

loop = c.app(concrete.Loop,
             keyword('loop'),
             c.many0(identifier),
             c.many0(value),
             cut('loop: missing close', keyword('stop')))

datum = c.app(concrete.Datum,
              identifier, 
              cut('datum: missing value', value))

save = c.app(concrete.Save,
             keyword('saveopen'),
             c.many0(datum),
             c.many0(loop),
             cut('save: missing close', keyword('saveclose')))

data = c.app(concrete.Data,
             keyword('dataopen'),
             c.many0(save))

end = c.not0(item)

nmrstar = c.seq2L(c.commit(data, 'data: unable to parse'), 
                  munch(cut('unparsed input remaining', end)))
