'''
@author: matt
'''
from ...examples.jsontree import (full)
from ...maybeerror import MaybeError
import unittest

error = MaybeError.error
pure = MaybeError.pure


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


class TestSuccess(unittest.TestCase):
    
    def testInteger(self):
        self.assertEqual(pure(888), full('888'))
    
    def testDecimal(self):
        self.assertEqual(pure(124.345), full('124.345'))
 
    def testNegativeNumber(self):
        self.assertEqual(pure(-345), full('-345'))
    
    def testPositiveExponent(self):
        self.assertEqual(pure(3.45e89), full('0.345e90'))
        self.assertEqual(pure(2e11), full('2e+11'))
        
    def testNegativeExponent(self):
        self.assertEqual(pure(8.23e-8), full('82.3e-9'))
    
    def testKeywords(self):
        self.assertEqual(pure(None), full('null'));
        self.assertEqual(pure(True), full('true'));
        self.assertEqual(pure(False), full('false'));
    
    def testString(self):
        self.assertEqual(pure(''), full('""'));
        self.assertEqual(pure('hello'), full('"hello"'));
        
    def testStringBasicEscape(self):
        self.assertEqual(pure('ab\n'), full('"ab\\n"'))
        the_str = '"\\\\\\/\\"\\b\\n\\r\\t\\f"'
        self.assertEqual(len(the_str), 18)
        self.assertEqual(pure('\\/"\b\n\r\t\f'), full(the_str))
        self.assertEqual(pure(8), full(the_str).fmap(len))
    
    def testStringUnicodeEscape(self):
        self.assertEqual(pure("afN"), full('"a\\u0066\\u004e"'))
    
    def testArray(self):
        self.assertEqual(pure([3.2, None, "h\n"]), full('  \n [3.2 , null, "h\\n"  ]  '))
        
    def testObject(self):
        self.assertEqual(pure({'': [], "abc": 1.3e3}), full('{"": [], "abc": 13e2  }  '))
