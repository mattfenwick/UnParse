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

def cst(type_, pos, **kwargs):
    kwargs['_type'] = type_
    kwargs['_pos'] = pos
    return kwargs

class TestJavaTokens(unittest.TestCase):
    
    def testFirst(self):
        self.assertTrue(False)
