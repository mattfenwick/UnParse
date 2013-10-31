'''
@author: matt
'''
from ...examples.jsontree import (full)
from ...maybeerror import MaybeError
import unittest

error = MaybeError.error


class TestErrors(unittest.TestCase):
    
    def testStringControlCharacter(self):
        inp = '"a\n"'
        self.assertEqual(error([('string', (1,1)), ('invalid control character', (1,3))]), 
                         full(inp))
        
    def testStringBadEscape(self):
        self.assertEqual(error([('string', (1,1)), ('invalid escape sequence', (1,3))]), 
                         full('"f\\qa"  '))

    def testObjectDuplicateKeys(self):
        self.assertEqual(error([('object', (1,1)), ('first key usage', (1,2)), ('duplicate key', (2,1))]), 
                         full('{"a": 2,\n"a": 3}'))

    def testObjectDuplicateKeysWithEscape(self):
        self.assertEqual(error([('object', (1,1)), ('first key usage', (1,2)), ('duplicate key', (2,1))]), 
                         full('{"A": 2,\n"\\u0041": 3}'))

    def testNumberTooBig(self): # just applies to decimals, or ints too?
        self.assertEqual(error([('number: floating-point overflow', (1,1))]), 
                         full('123e4353'))
        big_number = '3248972349823497234983274923847324897234982349723498327492384732489723498234972349832749238473248972349823497234983274923847324897234982349723498327492384732489723498234972349832749238473248972349823497234983274923847324897234982349723498327492384732489723498234972349832749238473248972349823497234983274923847'
        self.assertEqual(error([('number: floating-point overflow', (1,1))]), 
                         full(big_number))
        
    def testNumberLotsOfLeadingZeroes(self):
        self.assertEqual(error([('number: invalid leading 0', (1,1))]), 
                         full('01'))
        self.assertEqual(error([('number: invalid leading 0', (1,1))]), 
                         full('-001'))
    