'''
@author: mattf
'''
from ...examples.json import (json, jsonstring, number, 
                              oc, cc, os, cs, comma, colon, 
                              keyword, obj, array, keyVal)
from ... import maybeerror
from ... import combinators
import unittest


def good(rest, state, value):
    return maybeerror.MaybeError.pure({'rest': rest, 'state': state, 'result': value})

error = maybeerror.MaybeError.error

l = combinators.ConsList

def cst(name, state, **kwargs):
    kwargs['_name'] = name
    kwargs['_state'] = state
    return kwargs

def my_object(pos, seps, vals):
    return cst('object', pos, open='{', close='}', body={'separators': seps, 'values': vals})
    
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
        inp = '83 abc'
        self.assertEqual(good(l(inp[3:]), 
                              (1,4), 
                              cst('number', 
                                  (1,1), 
                                  sign=None, 
                                  integer=['8', '3'], 
                                  exponent=None, 
                                  decimal=None)), 
                         number.parse(l(inp), (1,1)))
        inp2 = '-77 abc'
        self.assertEqual(good(l(inp2[4:]), 
                              (1,5), 
                              cst('number', 
                                  (1,1),
                                  sign='-',
                                  integer=['7', '7'],
                                  exponent=None,
                                  decimal=None)), 
                         number.parse(l(inp2), (1,1)))
        
    def testDecimalAndExponent(self):
        inp = '-8.1e+2 abc'
        self.assertEqual(good(l(inp[8:]), (1,9), 
                              cst('number', (1,1),
                                  sign='-',
                                  integer=['8'],
                                  decimal=cst('decimal', (1,3),
                                              dot='.',
                                              digits=['1']),
                                  exponent=cst('exponent', (1,5),
                                               letter='e',
                                               sign='+',
                                               power=['2']))), 
                         number.parse(l(inp), (1,1)))
        inp2 = '-8.1 abc'
        self.assertEqual(good(l(inp2[5:]), (1,6), 
                              cst('number', (1,1),
                                  sign='-',
                                  integer=['8'],
                                  decimal=cst('decimal', (1,3),
                                              dot='.',
                                              digits=['1']),
                                  exponent=None)), 
                         number.parse(l(inp2), (1,1)))
        inp3 = '-8e+2 abc'
        self.assertEqual(good(l(inp3[6:]), (1,7), 
                              cst('number', (1,1),
                                  sign='-',
                                  integer=['8'],
                                  decimal=None,
                                  exponent=cst('exponent', (1,3),
                                               letter='e',
                                               sign='+',
                                               power=['2']))), 
                         number.parse(l(inp3), (1,1)))

    def testNumberMessedUpExponent(self):
        self.assertEqual(error([('number', (1,1)), ('exponent', (1,2)), ('power', (1,3))]), 
                         number.parse(l('0e abc'), (1,1)))

    def testLoneMinusSign(self):
        self.assertEqual(error([('number', (1,1)), ('digits', (1,2))]), 
                         number.parse(l('-abc'), (1,1)))
        
    def testEmptyString(self):
        inp = '"" def'
        self.assertEqual(good(l(inp[3:]), (1,4), cst('string', (1,1), open='"', close='"', value=[])), 
                         jsonstring.parse(l(inp), (1,1)))

    def testString(self):
        inp = '"abc" def'
        chars = [
            cst('character', (1,2), value='a'),
            cst('character', (1,3), value='b'),
            cst('character', (1,4), value='c')
        ]
        val = cst('string', (1,1), open='"', close='"', value=chars)
        self.assertEqual(good(l(inp[6:]), (1,7), val), jsonstring.parse(l(inp), (1,1)))
    
    def testStringBasicEscape(self):
        inp = '"a\\b\\nc" def'
        chars = [
            cst('character', (1,2), value='a'),
            cst('escape', (1,3), open='\\', value='b'),
            cst('escape', (1,5), open='\\', value='n'),
            cst('character', (1,7), value='c')
        ]
        val = cst('string', (1,1), open='"', close='"', value=chars)
        self.assertEqual(good(l(inp[9:]), (1,10), val), jsonstring.parse(l(inp), (1,1)))

    def testStringEscapeSequences(self):
        inp = '"\\"\\\\\\/\\b\\f\\n\\r\\t" def'
        chars = [
            cst('escape', (1,2), open='\\', value='"'),
            cst('escape', (1,4), open='\\', value='\\'),
            cst('escape', (1,6), open='\\', value='/'),
            cst('escape', (1,8), open='\\', value='b'),
            cst('escape', (1,10), open='\\', value='f'),
            cst('escape', (1,12), open='\\', value='n'),
            cst('escape', (1,14), open='\\', value='r'),
            cst('escape', (1,16), open='\\', value='t'),
        ]
        val = cst('string', (1,1), open='"', close='"', value=chars)
        self.assertEqual(good(l(inp[19:]), (1,20), val), jsonstring.parse(l(inp), (1,1)))
    
    def testStringUnicodeEscape(self):
        inp = '"a\\u0044n\\uabcdc" def'
        chars = [
            cst('character', (1,2), value='a'),
            cst('unicode escape', (1,3), open='\\u', value=['0','0','4','4']),
            cst('character', (1,9), value='n'),
            cst('unicode escape', (1,10), open='\\u', value=['a','b','c','d']),
            cst('character', (1,16), value='c')
        ]
        val = cst('string', (1,1), open='"', close='"', value=chars)
        self.assertEqual(good(l(inp[18:]), (1,19), val), jsonstring.parse(l(inp), (1,1)))

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
        self.assertEqual(good(l('abc'), (1,6), cst('keyword', (1,1), value='true')), 
                         keyword.parse(l('true abc'), (1,1)))
        self.assertEqual(good(l('abc'), (1,7), cst('keyword', (1,1), value='false')), 
                         keyword.parse(l('false abc'), (1,1)))
        self.assertEqual(good(l('abc'), (1,6), cst('keyword', (1,1), value='null')), 
                         keyword.parse(l('null abc'), (1,1)))
        
    def testKeyVal(self):
        chars = [
            cst('character', (1,2), value='q'),
            cst('character', (1,3), value='r'),
            cst('character', (1,4), value='s')
        ]
        self.assertEqual(good(l('abc'), 
                              (2,9),
                              cst('key/value pair', 
                                  (1,1),
                                  key=cst('string', (1,1), open='"', close='"', value=chars),
                                  colon=':',
                                  value=cst('keyword', (2,4), value='true'))), 
                         keyVal.parse(l('"qrs"\n : true abc'), (1,1)))
        
    def testKeyValueMissingColon(self):
        self.assertEqual(error([('key/value pair', (1,1)), ('colon', (1,6))]),
                         keyVal.parse(l('"qrs"} abc'), (1,1)))
        
    def testKeyValueMissingValue(self):
        self.assertEqual(error([('key/value pair', (1,1)), ('value', (1,10))]),
                         keyVal.parse(l('"qrs" :  abc'), (1,1)))

    def testObject(self):
        self.assertEqual(good(l('abc'), (1,4), my_object((1,1), [], [])), 
                         obj.parse(l('{} abc'), (1,1)))
        self.assertEqual(good(l('abc'), 
                              (1,12), 
                              my_object((1,1), [], 
                                        [cst('key/value pair', 
                                             (1,2),
                                             colon=':',
                                             key=cst('string', (1,2), open='"', close='"', value=[]),
                                             value=cst('keyword', (1,6), value='null'))])), 
                         obj.parse(l('{"": null} abc'), (1,1)))

    def testUnclosedObject(self): 
        e = error([('object', (1,1)), ('close', (1,12))])
        self.assertEqual(e, obj.parse(l('{"a": null '), (1,1)))
        self.assertEqual(e, obj.parse(l('{"a": null ,'), (1,1)))
        self.assertEqual(e, obj.parse(l('{"a": null ]'), (1,1)))

    def testArray(self):
        self.assertEqual(good(l('abc'), (1,4), 
                              cst('array', (1,1), open='[', close=']', 
                                  body={'values': [], 'separators': []})), 
                         array.parse(l('[] abc'), (1,1)))
        self.assertEqual(good(l([]), (1,7), 
                              cst('array', (1,1), open='[', close=']',
                                  body={'values': [cst('keyword', (1,2), value='true')],
                                        'separators': []})), 
                         array.parse(l('[true]'), (1,1)))
        self.assertEqual(good(l([]), (1,13), 
                              cst('array', (1,1), open='[', close=']',
                                  body={'values': [
                                            cst('keyword', (1,2), value='true'),
                                            cst('keyword', (1,7), value='false')
                                        ], 
                                        'separators': [',']})), 
                         array.parse(l('[true,false]'), (1,1)))

    def testArrayErrors(self):
        cases = ['[', '[2', '[2,']
        errors = [
            [('array', (1,1)), ('close', (1,2))],
            [('array', (1,1)), ('close', (1,3))],
            [('array', (1,1)), ('close', (1,3))]
        ]
        for (c, e) in zip(cases, errors):
            self.assertEqual(error(e),
                             array.parse(l(c), (1,1)))

    def testJson(self):
        self.assertEqual(good(l([]), 
                              (2,1), 
                              cst('json', (1,1), value=my_object((1,1), [], []))),
                         json.parse(l('{  }  \n'), (1,1)))
    
    def testUnclosedString(self):
        self.assertEqual(error([('string', (1,1)), ('double-quote', (1,5))]), jsonstring.parse(l('"abc'), (1,1)))

    def testStringBadUnicodeEscape(self):
        stack = [('string', (1,1)), ('unicode escape', (1,3)), ('4 hexadecimal digits', (1,5))]
        self.assertEqual(error(stack), 
                         jsonstring.parse(l('"2\\uabch1" def'), (1,1)))
        self.assertEqual(error(stack), 
                         jsonstring.parse(l('"?\\uab" def'), (1,1)))
    
    def testTrailingJunk(self):
        self.assertEqual(error([('unparsed input remaining', (1,4))]), json.parse(l('{} &'), (1,1)))

notyet = '''
    # errors

    def testJSONBadInputType(self): # should be unicode or something according to spec
        self.assertEqual(False)
'''
