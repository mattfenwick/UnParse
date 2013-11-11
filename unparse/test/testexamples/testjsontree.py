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
        self.assertEqual(full(inp),
                         error([('string', (1,1)), ('invalid control character', (1,3))]))
        
    def testStringBadEscape(self):
        self.assertEqual(full('"f\\qa"  '),
                         error([('string', (1,1)), ('invalid escape sequence', (1,3))]))

    def testObjectDuplicateKeys(self):
        self.assertEqual(full('{"a": 2,\n"a": 3}'),
                         error([('object', (1,1)), ('first key usage', (1,2)), ('duplicate key', (2,1))]))

    def testObjectDuplicateKeysWithEscape(self):
        self.assertEqual(full('{"A": 2,\n"\\u0041": 3}'),
                         error([('object', (1,1)), ('first key usage', (1,2)), ('duplicate key', (2,1))]))

    def testNumberTooBig(self): # just applies to decimals, or ints too?
        self.assertEqual(full('123e4353'),
                         error([('number: floating-point overflow', (1,1))]))
        big_number = '3248972349823497234983274923847324897234982349723498327492384732489723498234972349832749238473248972349823497234983274923847324897234982349723498327492384732489723498234972349832749238473248972349823497234983274923847324897234982349723498327492384732489723498234972349832749238473248972349823497234983274923847'
        self.assertEqual(full(big_number),
                         error([('number: floating-point overflow', (1,1))]))
        
    def testNumberLotsOfLeadingZeroes(self):
        self.assertEqual(full('01'), 
                         error([('number: invalid leading 0', (1,1))]))
        self.assertEqual(full('-001'), 
                         error([('number: invalid leading 0', (1,1))]))


class TestSuccess(unittest.TestCase):
    
    def testInteger(self):
        self.assertEqual(full('888'), pure(888))
    
    def testDecimal(self):
        self.assertEqual(full('124.345'), pure(124.345))
 
    def testNegativeNumber(self):
        self.assertEqual(full('-345'), pure(-345))
    
    def testPositiveExponent(self):
        self.assertEqual(full('0.345e90'), pure(3.45e89))
        self.assertEqual(full('2e+11'), pure(2e11))
        
    def testNegativeExponent(self):
        self.assertEqual(full('82.3e-9'), pure(8.23e-8))
    
    def testKeywords(self):
        self.assertEqual(full('null'), pure(None))
        self.assertEqual(full('true'), pure(True))
        self.assertEqual(full('false'), pure(False))
    
    def testString(self):
        self.assertEqual(full('""'), pure(''))
        self.assertEqual(full('"hello"'), pure('hello'))
        
    def testStringBasicEscape(self):
        self.assertEqual(full('"ab\\n"'), pure('ab\n'))
        the_str = '"\\\\\\/\\"\\b\\n\\r\\t\\f"'
        self.assertEqual(len(the_str), 18)
        self.assertEqual(full(the_str), pure('\\/"\b\n\r\t\f'))
        self.assertEqual(full(the_str).fmap(len), pure(8))
    
    def testStringUnicodeEscape(self):
        self.assertEqual(full('"a\\u0066\\u004e"'), pure("afN"))
    
    def testArray(self):
        self.assertEqual(full('  \n [3.2 , null, "h\\n"  ]  '), pure([3.2, None, "h\n"]))
        
    def testObject(self):
        self.assertEqual(full('{"": [], "abc": 13e2  }  '), pure({'': [], "abc": 1.3e3}))
