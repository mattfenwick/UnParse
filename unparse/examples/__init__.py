from __future__ import print_function
from .. import combinators
#from . import woof as woofstandard
#from .woofpos import (app, wlist, special, woof)
#from .json import (json, number, whitespace, jsonstring, keyword, array, obj)



def runParser(parser, inp):
    result = combinators.run(parser, inp, (1,1))
    if result.status == 'success':
        return result.value['result']
    elif result.status == 'failure':
        raise ValueError('oops -- parsing failed softly.  that was unexpected')
    else: # status is error
        print('error during parsing:')
        for (message, (line, column)) in result.value:
            print('  %s at line %i, column %i' % (message, line, column))
        raise ValueError('oops, parsing failed with an error')
