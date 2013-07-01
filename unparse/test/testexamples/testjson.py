'''
@author: mattf
'''
from ...examples.json import (json, jsonstring, number, oc, cc, os, cs, comma, colon, boolean, null, obj, array)
from ... import maybeerror
from ... import conslist
import unittest


def good(rest, state, value):
    return maybeerror.MaybeError.pure({'rest': rest, 'state': state, 'result': value})

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
    
    def testNumber(self):
        # sign
        # int body
        # optional decimal
        # optional exponent
        pass

    def testString(self):
        inp = '"abc" def'
        self.assertEqual(good(l(inp[5:]), (1,6), 'abc'), jsonstring.parse(l(inp), (1,1)))
    
    def testStringBasicEscape(self):
        inp = '"a\\b\\nc" def'
        self.assertEqual(good(l(inp[8:]), (1,9), 'a\b\nc'), jsonstring.parse(l(inp), (1,1)))
    
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

    def testBoolean(self):
        self.assertEqual(good(l(' abc'), (1,5), True), boolean.parse(l('true abc'), (1,1)))
        self.assertEqual(good(l(' abc'), (1,6), False), boolean.parse(l('false abc'), (1,1)))

    def testNull(self):
        self.assertEqual(good(l(' abc'), (1,5), None), null.parse(l('null abc'), (1,1)))
        
    def testObject(self):
        self.assertEqual(good(l('abc'), (1,4), []), obj.parse(l('{} abc'), (1,1)))
        self.assertEqual(good(l([]), (1,12), [('a', None)]), obj.parse(l('{"a": null}'), (1,1)))
        inp = '{"abc": 123, "def": 456}, null abc'
        self.assertEqual(good(l(inp[24:]), (1,25), [('abc', 123), ('def', 456)]), obj.parse(l(inp), (1,1)))

    def testArray(self):
        self.assertEqual(good(l('abc'), (1,4), []), array.parse(l('[] abc'), (1,1)))
        self.assertEqual(good(l([]), (1,7), [True]), array.parse(l('[true]'), (1,1)))
        inp = '["abc", 123], null abc'
        self.assertEqual(good(l(inp[12:]), (1,13), ['abc', 123]), array.parse(l(inp), (1,1)))

    def testJson(self):
        self.assertEqual(good(l([]), (3,1), [('abc', [True, None]), ('def', 32)]), json.parse(l('{ "abc" : [ true , null ] , \n "def": 32 }  \n'), (1,1)))

notyet = '''
    # errors
    def testNumberTooBig(self): # just applies to decimals, or ints too?
        self.assertEqual(False)

    def testUnclosedString(self):
        self.assertEqual(False)

    def testStringBadEscape(self):
        self.assertEqual(False)
    
    def testStringControlCharacter(self): # i.e. "\n" or something
        self.assertTrue(False)

    def testStringBadUnicodeEscape(self): # i.e. "\uabch" or "\uab"
        self.assertEqual(False)

    def testUnclosedArray(self):
        self.assertEqual(False)

    def testObjectDuplicateKeys(self):
        self.assertEqual(False)

    def testKeyValueMissingColon(self):
        self.assertEqual(False)

    def testKeyValueMissingValue(self):
        self.assertEqual(False)

    def testUnclosedObject(self): # cases: {"a":      {"a"     {"a": b     {"a":b,     {"a": b ] } 
        self.assertEqual(False)

    def testNumberLotsOfLeadingZeroes(self):
        self.assertEqual(False)

    def testJSONBadInputType(self): # should be unicode or something according to spec
        self.assertEqual(False)
    
    def testTrailingJunk(self):
        self.assertEqual(False)
'''
