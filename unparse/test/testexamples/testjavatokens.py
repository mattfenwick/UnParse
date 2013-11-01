'''
@author: mattf
'''
from ...examples.javatokens import (tokenizer)
from ...maybeerror import MaybeError
from ... import combinators
import unittest


def good(rest, state, value):
    return MaybeError.pure({'rest': rest, 'state': state, 'result': value})

error = MaybeError.error

l = combinators.ConsList

def cst(name, state, **kwargs):
    kwargs['_name'] = name
    kwargs['_state'] = state
    return kwargs

class TestJavaTokens(unittest.TestCase):
    
    def testFirst(self):
        self.assertTrue(False)
