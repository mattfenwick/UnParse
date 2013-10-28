'''
@author: matt
'''
from ...examples.jsontree import (full)
from ... import maybeerror
import unittest


class TestTree(unittest.TestCase):
    
    def testFirst(self):
        oops('unimplemented')


class TestErrors(unittest.TestCase):
    
    def testStringControlCharacter(self):
        inp = '"a\n" def'
        self.assertEqual(error([('string', (1,1)), ('illegal control character', (1,3))]), jsonstring.parse(l(inp), (1,1)))
        
    def testStringBadEscape(self):
        self.assertEqual(error([('string', (1,1)), ('illegal escape', (1,4))]), 
                         jsonstring.parse(l('"f\\qa" abc'), (1,1)))

    def testObjectDuplicateKeys(self):
        self.assertEqual(error([('object', (1,1)), ('duplicate key: a', (2,1))]), 
                         obj.parse(l('{"a": 2,\n"a": 3}'), (1,1)))

    def testObjectDuplicateKeysWithEscape(self):
        self.assertEqual(error([('object', (1,1)), ('duplicate key: A', (2,1))]), 
                         obj.parse(l('{"A": 2,\n"\\u0041": 3}'), (1,1)))

    def testNumberTooBig(self): # just applies to decimals, or ints too?
        self.assertEqual(error([('number', (1,1)), ('floating-point overflow', (1,14))]), 
                         number.parse(l('123e435321532 abc'), (1,1)))
        big_number = '3248972349823497234983274923847324897234982349723498327492384732489723498234972349832749238473248972349823497234983274923847324897234982349723498327492384732489723498234972349832749238473248972349823497234983274923847324897234982349723498327492384732489723498234972349832749238473248972349823497234983274923847'
        self.assertEqual(error([('number', (1,1)), ('floating-point overflow', (1,311))]), 
                         number.parse(l(big_number + ' abc'), (1,1)))
        
    def testNumberLotsOfLeadingZeroes(self):
        self.assertEqual(error([('number', (1,1)), ('leading 0', (1,3))]), 
                         number.parse(l('01 abc'), (1,1)))
        self.assertEqual(error([('number', (1,1)), ('leading 0', (1,5))]), 
                         number.parse(l('-001 abc'), (1,1)))
    