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

def cst(name, start, end, **kwargs):
    kwargs['_name'] = name
    kwargs['_start'] = start
    kwargs['_end'] = end
    return kwargs


def my_object(start, end, body):
    return cst('object', start, end, open='{', close='}', body=body)
    
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
        self.assertEqual(number.parse(l(inp), (1,1)),
                         good(l(inp[3:]), 
                              (1,4), 
                              cst('number', 
                                  (1,1), 
                                  (1,3),
                                  sign=None, 
                                  integer=['8', '3'], 
                                  exponent=None, 
                                  decimal=None)))
        inp2 = '-77 abc'
        self.assertEqual(number.parse(l(inp2), (1,1)),
                         good(l(inp2[4:]), 
                              (1,5), 
                              cst('number', 
                                  (1,1),
                                  (1,4),
                                  sign='-',
                                  integer=['7', '7'],
                                  exponent=None,
                                  decimal=None)))

    def testDecimalAndExponent(self):
        inp = '-8.1e+2 abc'
        self.assertEqual(number.parse(l(inp), (1,1)),
                         good(l(inp[8:]), (1,9), 
                              cst('number', (1,1), (1,8),
                                  sign='-',
                                  integer=['8'],
                                  decimal=cst('decimal', (1,3), (1,5),
                                              dot='.',
                                              digits=['1']),
                                  exponent=cst('exponent', (1,5), (1,8),
                                               letter='e',
                                               sign='+',
                                               power=['2']))))
        inp2 = '-8.1 abc'
        self.assertEqual(number.parse(l(inp2), (1,1)),
                         good(l(inp2[5:]), (1,6), 
                              cst('number', (1,1), (1,5),
                                  sign='-',
                                  integer=['8'],
                                  decimal=cst('decimal', (1,3), (1,5),
                                              dot='.',
                                              digits=['1']),
                                  exponent=None)))
        inp3 = '-8e+2 abc'
        self.assertEqual(number.parse(l(inp3), (1,1)),
                         good(l(inp3[6:]), (1,7), 
                              cst('number', (1,1), (1,6),
                                  sign='-',
                                  integer=['8'],
                                  decimal=None,
                                  exponent=cst('exponent', (1,3), (1,6),
                                               letter='e',
                                               sign='+',
                                               power=['2']))))

    def testNumberMessedUpExponent(self):
        self.assertEqual(number.parse(l('0e abc'), (1,1)),
                         error([('number', (1,1)), ('exponent', (1,2)), ('power', (1,3))]))

    def testLoneMinusSign(self):
        self.assertEqual(number.parse(l('-abc'), (1,1)),
                         error([('number', (1,1)), ('digits', (1,2))]))
        
    def testEmptyString(self):
        inp = '"" def'
        self.assertEqual(jsonstring.parse(l(inp), (1,1)),
                         good(l(inp[3:]), (1,4), cst('string', (1,1), (1,3), open='"', close='"', value=[])))

    def testString(self):
        inp = '"abc" def'
        chars = [
            cst('character', (1,2), (1,3), value='a'),
            cst('character', (1,3), (1,4), value='b'),
            cst('character', (1,4), (1,5), value='c')
        ]
        val = cst('string', (1,1), (1,6), open='"', close='"', value=chars)
        self.assertEqual(jsonstring.parse(l(inp), (1,1)), good(l(inp[6:]), (1,7), val))

    def testStringBasicEscape(self):
        inp = '"a\\b\\nc" def'
        chars = [
            cst('character', (1,2), (1,3), value='a'),
            cst('escape', (1,3), (1,5), open='\\', value='b'),
            cst('escape', (1,5), (1,7), open='\\', value='n'),
            cst('character', (1,7), (1,8), value='c')
        ]
        val = cst('string', (1,1), (1,9), open='"', close='"', value=chars)
        self.assertEqual(jsonstring.parse(l(inp), (1,1)), good(l(inp[9:]), (1,10), val))

    def testStringEscapeSequences(self):
        inp = '"\\"\\\\\\/\\b\\f\\n\\r\\t" def'
        chars = [
            cst('escape', (1,2), (1,4), open='\\', value='"'),
            cst('escape', (1,4), (1,6), open='\\', value='\\'),
            cst('escape', (1,6), (1,8), open='\\', value='/'),
            cst('escape', (1,8), (1,10), open='\\', value='b'),
            cst('escape', (1,10), (1,12), open='\\', value='f'),
            cst('escape', (1,12), (1,14), open='\\', value='n'),
            cst('escape', (1,14), (1,16), open='\\', value='r'),
            cst('escape', (1,16), (1,18), open='\\', value='t'),
        ]
        val = cst('string', (1,1), (1,19), open='"', close='"', value=chars)
        self.assertEqual(jsonstring.parse(l(inp), (1,1)), good(l(inp[19:]), (1,20), val))
   
    def testStringUnicodeEscape(self):
        inp = '"a\\u0044n\\uabcdc" def'
        chars = [
            cst('character', (1,2), (1,3), value='a'),
            cst('unicode escape', (1,3), (1,9), open='\\u', value=['0','0','4','4']),
            cst('character', (1,9), (1,10), value='n'),
            cst('unicode escape', (1,10), (1,16), open='\\u', value=['a','b','c','d']),
            cst('character', (1,16), (1,17), value='c')
        ]
        val = cst('string', (1,1), (1,18), open='"', close='"', value=chars)
        self.assertEqual(jsonstring.parse(l(inp), (1,1)), good(l(inp[18:]), (1,19), val))

    def testPunctuation(self):
        cases = [['{ abc', oc],
                 ['} abc', cc],
                 ['[ abc', os],
                 ['] abc', cs],
                 [', abc', comma],
                 [': abc', colon]]
        for (inp, parser) in cases:
#            print inp
            self.assertEqual(parser.parse(l(inp), (1,1)), good(l(inp[2:]), (1,3), inp[0]))

    def testKeyword(self):
        self.assertEqual(keyword.parse(l('true abc'), (1,1)),
                         good(l('abc'), (1,6), cst('keyword', (1,1), (1,5), value='true')))
        self.assertEqual(keyword.parse(l('false abc'), (1,1)),
                         good(l('abc'), (1,7), cst('keyword', (1,1), (1,6), value='false')))
        self.assertEqual(keyword.parse(l('null abc'), (1,1)),
                         good(l('abc'), (1,6), cst('keyword', (1,1), (1,5), value='null')))
        
    def testKeyVal(self):
        chars = [
            cst('character', (1,2), (1,3), value='q'),
            cst('character', (1,3), (1,4), value='r'),
            cst('character', (1,4), (1,5), value='s')
        ]
        self.assertEqual(keyVal.parse(l('"qrs"\n : true abc'), (1,1)),
                         good(l('abc'), 
                              (2,9),
                              cst('key/value pair', 
                                  (1,1),
                                  (2,9), 
                                  key=cst('string', (1,1), (1,6), open='"', close='"', value=chars),
                                  colon=':',
                                  value=cst('keyword', (2,4), (2,8), value='true'))))

    def testKeyValueMissingColon(self):
        self.assertEqual(keyVal.parse(l('"qrs"} abc'), (1,1)),
                         error([('key/value pair', (1,1)), ('colon', (1,6))]))
        
    def testKeyValueMissingValue(self):
        self.assertEqual(keyVal.parse(l('"qrs" :  abc'), (1,1)),
                         error([('key/value pair', (1,1)), ('value', (1,10))]))

    def testObject(self):
        self.assertEqual(obj.parse(l('{} abc'), (1,1)),
                         good(l('abc'), (1,4), my_object((1,1), (1,4), None)))
        self.assertEqual(obj.parse(l('{"": null} abc'), (1,1)),
                         good(l('abc'), 
                              (1,12), 
                              my_object((1,1), (1,12), (cst('key/value pair', 
                                             (1,2), (1,10),
                                             colon=':',
                                             key=cst('string', (1,2), (1,4), open='"', close='"', value=[]),
                                             value=cst('keyword', (1,6), (1,10), value='null')), []))))

    def testUnclosedObject(self): 
        e = error([('object', (1,1)), ('close', (1,12))])
        self.assertEqual(obj.parse(l('{"a": null '), (1,1)), e)
        self.assertEqual(obj.parse(l('{"a": null ,'), (1,1)), e)
        self.assertEqual(obj.parse(l('{"a": null ]'), (1,1)), e)

    def testArray(self):
        self.assertEqual(array.parse(l('[] abc'), (1,1)),
                         good(l('abc'), (1,4), 
                              cst('array', (1,1), (1,4), open='[', close=']', 
                                  body=None)))
        self.assertEqual(array.parse(l('[true]'), (1,1)),
                         good(l([]), (1,7), 
                              cst('array', (1,1), (1,7), open='[', close=']',
                                  body=(cst('keyword', (1,2), (1,6), value='true'), []))))
        self.assertEqual(array.parse(l('[true,false]'), (1,1)),
                         good(l([]), (1,13), 
                              cst('array', (1,1), (1,13), open='[', close=']',
                                  body=(cst('keyword', (1,2), (1,6), value='true'),
                                        [(',', cst('keyword', (1,7), (1,12), value='false'))]))))

    def testArrayErrors(self):
        cases = ['[', '[2', '[2,']
        errors = [
            [('array', (1,1)), ('close', (1,2))],
            [('array', (1,1)), ('close', (1,3))],
            [('array', (1,1)), ('close', (1,3))]
        ]
        for (c, e) in zip(cases, errors):
            self.assertEqual(array.parse(l(c), (1,1)),
                             error(e))

    def testJson(self):
        self.assertEqual(json.parse(l('{  }  \n'), (1,1)),
                         good(l([]), 
                              (2,1), 
                              cst('json', (1,1), (2,1), value=my_object((1,1), (2,1), None))))

    def testNoJson(self):
        self.assertEqual(json.parse(l('a'), (1,1)),
                         error([('json value', (1,1))]))
    
    def testUnclosedString(self):
        self.assertEqual(jsonstring.parse(l('"abc'), (1,1)),
                         error([('string', (1,1)), ('double-quote', (1,5))]))

    def testStringBadUnicodeEscape(self):
        stack = [('string', (1,1)), ('unicode escape', (1,3)), ('4 hexadecimal digits', (1,5))]
        self.assertEqual(jsonstring.parse(l('"2\\uabch1" def'), (1,1)),
                         error(stack))
        self.assertEqual(jsonstring.parse(l('"?\\uab" def'), (1,1)),
                         error(stack))
    
    def testTrailingJunk(self):
        self.assertEqual(json.parse(l('{} &'), (1,1)),
                         error([('unparsed input remaining', (1,4))]))

notyet = '''
    # errors

    def testJSONBadInputType(self): # should be unicode or something according to spec
        self.assertEqual(False)
'''


if __name__ == "__main__":
    unittest.main()
