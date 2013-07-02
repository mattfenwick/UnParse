'''
@author: mattf
'''
from ...examples.json import (json, jsonstring, number, oc, cc, os, cs, comma, colon, keyword, obj, array, keyVal)
from ... import maybeerror
from ... import conslist
import unittest


def good(rest, state, value):
    return maybeerror.MaybeError.pure({'rest': rest, 'state': state, 'result': value})

error = maybeerror.MaybeError.error

l = conslist.ConsList.fromIterable

#
# Value   :=  'false'  |  'null'  |  'true'  |  Object  |  Array  |  Number  |  String
# 
# Object  :=  '{'  sepBy0(pair, ',')  '}'
#   where pair  :=  String  ':'  Value
# 
# Array   :=  '['  sepBy0(Value, ',')  ']'
# 
# Number  :=  '-'(?)  body  frac(?)  exponent(?)
#   where body   :=  '0'  |  ( [1-9]  [0-9](*) )
#         frac   :=  '.'  [0-9](+)
#         exponent  :=  [eE]  [-+](?)  [0-9](+)
# 
# String  :=  '"'  ( char  |  escape  |  unicode )(*)  '"'
#   where char    :=  not1( '\\'  |  '"'  |  \u0000-\u001F )
#         escape  :=  '\\'  ["\/bfnrt]                            <-- that's 8 characters
#         unicode :=  '\\u'  [0-9a-eA-E](4)

class TestJson(unittest.TestCase):
    
    def testInteger(self):
        inp = '839001 abc'
        self.assertEqual(good(l(inp[6:]), (1,7), 839001), number.parse(l(inp), (1,1)))
        inp2 = '-7777 abc'
        self.assertEqual(good(l(inp2[5:]), (1,6), -7777), number.parse(l(inp2), (1,1)))
        self.assertEqual(good(l('abc'), (1,2), 0), number.parse(l('0abc'), (1,1)))
        self.assertEqual(good(l('abc'), (1,3), 0), number.parse(l('-0abc'), (1,1)))
        
    def testDecimal(self):
        inp = '839.001 abc'
        self.assertEqual(good(l(inp[7:]), (1,8), 839.001), number.parse(l(inp), (1,1)))
        inp2 = '-77e77 abc'
        self.assertEqual(good(l(inp2[6:]), (1,7), -7.7e78), number.parse(l(inp2), (1,1)))
        self.assertEqual(good(l('abc'), (1,4), 0), number.parse(l('0e2abc'), (1,1)))
        self.assertEqual(good(l('abc'), (1,7), 0), number.parse(l('-0.000abc'), (1,1)))

    def testNumberTooBig(self): # just applies to decimals, or ints too?
        self.assertEqual(error([('number', (1,1)), ('floating-point overflow', (1,14))]), 
                         number.parse(l('123e435321532 abc'), (1,1)))
        
    def testNumberLotsOfLeadingZeroes(self):
        self.assertEqual(error([('number', (1,1)), ('leading 0', (1,3))]), 
                         number.parse(l('01 abc'), (1,1)))
        self.assertEqual(error([('number', (1,1)), ('leading 0', (1,5))]), 
                         number.parse(l('-001 abc'), (1,1)))
    
    def testNumberMessedUpExponent(self):
        self.assertEqual(error([('number', (1,1)), ('expected exponent', (1,3))]), 
                         number.parse(l('0e abc'), (1,1)))

    def testLoneMinusSign(self):
        self.assertEqual(error([('number', (1,1)), ('expected digits', (1,2))]), 
                         number.parse(l('-abc'), (1,1)))
        
    def testEmptyString(self):
        inp = '"" def'
        self.assertEqual(good(l(inp[2:]), (1,3), ''), jsonstring.parse(l(inp), (1,1)))

    def testString(self):
        inp = '"abc" def'
        self.assertEqual(good(l(inp[5:]), (1,6), 'abc'), jsonstring.parse(l(inp), (1,1)))
    
    def testStringBasicEscape(self):
        inp = '"a\\b\\nc" def'
        self.assertEqual(good(l(inp[8:]), (1,9), 'a\b\nc'), jsonstring.parse(l(inp), (1,1)))

    def testStringEscapeSequences(self):
        inp = '"\\"\\\\\\/\\b\\f\\n\\r\\t" def'
        self.assertEqual(good(l(inp[18:]), (1,19), '"\\/\b\f\n\r\t'), jsonstring.parse(l(inp), (1,1)))
    
    def testStringUnicodeEscape(self):
        inp = '"a\\u0044n\\uabcdc" def'
        self.assertEqual(good(l(inp[17:]), (1,18), u'aDn\uabcdc'), jsonstring.parse(l(inp), (1,1)))

    def testPunctuation(self):
        cases = [['{ abc', oc],
                 ['} abc', cc],
                 ['[ abc', os],
                 ['] abc', cs],
                 [', abc', comma],
                 [': abc', colon]]
        for (inp, parser) in cases:
            print inp
            self.assertEqual(good(l(inp[2:]), (1,3), inp[0]), parser.parse(l(inp), (1,1)))

    def testKeyword(self):
        self.assertEqual(good(l(' abc'), (1,5), True), keyword.parse(l('true abc'), (1,1)))
        self.assertEqual(good(l(' abc'), (1,6), False), keyword.parse(l('false abc'), (1,1)))
        self.assertEqual(good(l(' abc'), (1,5), None), keyword.parse(l('null abc'), (1,1)))
        
    def testKeyVal(self):
        self.assertEqual(good(l('abc'), (2,6), ((1,1), 'qrs', 3)),
                         keyVal.parse(l('"qrs"\n : 3 abc'), (1,1)))
        
    def testKeyValueMissingColon(self):
        self.assertEqual(error([('key/value pair', (1,1)), ('expected :', (1,6))]),
                         keyVal.parse(l('"qrs"} abc'), (1,1)))
        
    def testKeyValueMissingValue(self):
        self.assertEqual(error([('key/value pair', (1,1)), ('expected value', (1,10))]),
                         keyVal.parse(l('"qrs" :  abc'), (1,1)))

    def testObject(self):
        self.assertEqual(good(l('abc'), (1,4), {}), obj.parse(l('{} abc'), (1,1)))
        self.assertEqual(good(l('abc'), (1,9), {'': 3}), obj.parse(l('{"": 3} abc'), (1,1)))
        self.assertEqual(good(l([]), (1,12), {'a': None}), obj.parse(l('{"a": null}'), (1,1)))
        inp = '{"abc": 123, "def": 456}, null abc'
        self.assertEqual(good(l(inp[24:]), (1,25), {'abc': 123, 'def': 456}), obj.parse(l(inp), (1,1)))

    def testObjectDuplicateKeys(self):
        self.assertEqual(error([('object', (1,1)), ('duplicate key: a', (2,1))]), 
                         obj.parse(l('{"a": 2,\n"a": 3}'), (1,1)))

    def testObjectDuplicateKeysWithEscape(self):
        self.assertEqual(error([('object', (1,1)), ('duplicate key: A', (2,1))]), 
                         obj.parse(l('{"A": 2,\n"\\u0041": 3}'), (1,1)))

    def testUnclosedObject(self): 
        e = error([('object', (1,1)), ('expected }', (1,12))])
        self.assertEqual(e, obj.parse(l('{"a": null '), (1,1)))
        self.assertEqual(e, obj.parse(l('{"a": null ,'), (1,1)))
        self.assertEqual(e, obj.parse(l('{"a": null ]'), (1,1)))

    def testArray(self):
        self.assertEqual(good(l('abc'), (1,4), []), array.parse(l('[] abc'), (1,1)))
        self.assertEqual(good(l([]), (1,7), [True]), array.parse(l('[true]'), (1,1)))
        inp = '["abc", 123], null abc'
        self.assertEqual(good(l(inp[12:]), (1,13), ['abc', 123]), array.parse(l(inp), (1,1)))

    def testUnclosedArray(self):
        self.assertEqual(error([('array', (1,1)), ('expected ]', (1,5))]), 
                         array.parse(l('[2,3'), (1,1)))

    def testJson(self):
        self.assertEqual(good(l([]), (3,1), {'abc': [True, None], 'def': 32}), 
                         json.parse(l('{ "abc" : [ true , null ] , \n "def": 32 }  \n'), (1,1)))
    
    def testStringControlCharacter(self):
        inp = '"a\n" def'
        self.assertEqual(error([('string', (1,1)), ('illegal control character', (1,3))]), jsonstring.parse(l(inp), (1,1)))

    def testUnclosedString(self):
        self.assertEqual(error([('string', (1,1)), ('expected "', (1,5))]), jsonstring.parse(l('"abc'), (1,1)))

    def testStringBadEscape(self):
        self.assertEqual(error([('string', (1,1)), ('illegal escape', (1,4))]), jsonstring.parse(l('"f\\qa" abc'), (1,1)))

    def testStringBadUnicodeEscape(self):
        self.assertEqual(error([('string', (1,1)), ('invalid hex escape sequence', (1,5))]), jsonstring.parse(l('"2\\uabch1" def'), (1,1)))
        self.assertEqual(error([('string', (1,1)), ('invalid hex escape sequence', (1,4))]), jsonstring.parse(l('"\\uab" def'), (1,1)))
    
    def testTrailingJunk(self):
        self.assertEqual(error([('unparsed input remaining', (1,4))]), json.parse(l('{} &'), (1,1)))

notyet = '''
    # errors

    def testJSONBadInputType(self): # should be unicode or something according to spec
        self.assertEqual(False)
'''
