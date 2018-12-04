'''
@author: mattf
'''
from ...examples.javatokens import (tokenizer)
from ...maybeerror import MaybeError
from ... import combinators
import unittest


l = combinators.ConsList

def cst(name, state, **kwargs):
    kwargs['_name'] = name
    kwargs['_state'] = state
    return kwargs

class TestJavaTokens(unittest.TestCase):
    
    def testFirst(self):
        parsed = combinators.run(tokenizer, '1, 2')
        self.assertEqual(parsed.status, 'success')
        self.assertEqual(len(parsed.value['result']), 4)


if __name__ == "__main__":
    unittest.main()
