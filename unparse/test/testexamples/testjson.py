'''
@author: mattf
'''
from ...examples.json import (json, jsonstring, number, oc, cc, os, cs, comma, colon, keyword, obj, array)
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
    
    def testNumber(self):
        # sign
        # int body
        # optional decimal
        # optional exponent
        pass

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

    def testArray(self):
        self.assertEqual(good(l('abc'), (1,4), []), array.parse(l('[] abc'), (1,1)))
        self.assertEqual(good(l([]), (1,7), [True]), array.parse(l('[true]'), (1,1)))
        inp = '["abc", 123], null abc'
        self.assertEqual(good(l(inp[12:]), (1,13), ['abc', 123]), array.parse(l(inp), (1,1)))

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
    def testNumberTooBig(self): # just applies to decimals, or ints too?
        self.assertEqual(False)

    def testUnclosedArray(self):
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
'''
