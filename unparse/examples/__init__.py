from .nmrstar import (nmrstar)
from . import woof as woofstandard
from .woofpos import (app, wlist, special, woof)
from .. import conslist
from .json import (json, number, whitespace, jsonstring, boolean, null, array, obj)



def runParser(parser, inp):
    result = parser.parse(conslist.ConsList(inp, 0), (1, 1))
    if result.status == 'success':
        return result.value['result']
    elif result.status == 'failure':
        raise ValueError('oops -- parsing failed softly.  that was unexpected')
    else: # status is error
        print 'error during parsing:'
        for (message, (line, column)) in result.value:
            print '  %s at line %i, column %i' % (message, line, column)
        raise ValueError('oops, parsing failed with an error')


def runP(parser, inp):
    return parser.parse(conslist.ConsList(inp, 0), (1, 1))