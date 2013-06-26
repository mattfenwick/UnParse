from .. import standard as s
from .. import conslist as c
from .. import maybeerror as me
import unittest as u


p = s.Parser
m = me.MaybeError

l = c.ConsList.fromIterable

def good(rest, state, result):
    return m.pure({'rest': rest, 'state': state, 'result': result})


class TestParser(u.TestCase):
    
    def testFmap(self):
        f = lambda x: x + 7
        v1 = p.pure(3).fmap(f).parse('ab', 81)
        self.assertEqual(good('ab', 81, 10), v1)
        v2 = p.zero.fmap(f).parse('ab', 81)
        self.assertEqual(m.zero, v2)
        v3 = p.error('oops').fmap(f).parse('ab', 81)
        self.assertEqual(m.error('oops'), v3)
        
    def testPure(self):
        val = p.pure(3).parse('abc', 2)
        self.assertEqual(good('abc', 2, 3), val)
    
    def testBind(self):
        two = p.item.bind(lambda x: p.literal(x))
        self.assertEqual(two.parse(l('abcde'), {}), m.zero)
        self.assertEqual(two.parse(l('aabcde'), {}), good(l('bcde'), {}, 'a'))
        
    def testPlus(self):
        g1, g2, b, e = p.pure(3), p.pure('hi'), p.zero, p.error('oops')
        self.assertEqual(g1.plus(g2).parse('abc', None), g1.parse('abc', None))
        self.assertEqual(b.plus(g2).parse('abc', 3), g2.parse('abc', 3))
        self.assertEqual(e.plus(g1).parse('abc', 4), e.parse('abc', 4))
    
    def testError(self):
        v1 = p.error('uh-oh').parse('abc', 123)
        self.assertEqual(m.error('uh-oh'), v1)
    
    def testCatchError(self):
        f1 = lambda e: p.pure(3)
        f2 = lambda e: p.error('dead again')
        # error -> good -- resumes parsing with tokens and state from before the error occurred
        self.assertEqual(good('123', [2,4], 3), p.error('dead 1').catchError(f1).parse('123', [2, 4]))
        # good -> good (unaffected by this combinator)
        self.assertEqual(good('123', [2,4], 18), p.pure(18).catchError(f1).parse('123', [2,4]))
        # error -> error
        self.assertEqual(m.error('dead again'), p.error('dead 1').catchError(f2).parse('123', [2,4]))
        # good -> error is not possible with this combinator
        
    def testMapError(self):
        f = len
        v1 = p.error('abcdef').mapError(f).parse('123abc', None)
        self.assertEqual(m.error(6), v1)
        v2 = p.zero.mapError(f).parse('123abc', None)
        self.assertEqual(m.zero, v2)
        v3 = p.pure(82).mapError(f).parse('123abc', None)
        self.assertEqual(good('123abc', None, 82), v3)        

    def testPut(self):
        val = p.put('xyz')
        self.assertEqual(val.parse('abc', []), good('xyz', [], None))
    
    def testPutState(self):
        v1 = p.putState(29).parse('abc123', 2)
        self.assertEqual(good('abc123', 29, None), v1)
    
    def testUpdateState(self):
        v1 = p.updateState(lambda x: x * 4).parse('abc', 18)
        self.assertEqual(good('abc', 72, None), v1)
        
    def testCheck(self):
        val = p.get.check(lambda x: len(x) > 3)
        self.assertEqual(val.parse('abcde', []), good('abcde', [], 'abcde'))
        self.assertEqual(val.parse('abc', []), m.zero)
    
    def testLiteral(self):
        val = p.literal(3)
        self.assertEqual(val.parse(l([3,4,5]), {}), good(l([4,5]), {}, 3))
        self.assertEqual(val.parse(l([4,5]), {}), m.zero)
    
    def testSatisfy(self):
        v1 = p.satisfy(lambda x: x > 3).parse(l([1,2,3]), 'bye')
        self.assertEqual(m.zero, v1)
        v2 = p.satisfy(lambda x: x < 3).parse(l([1,2,3]), 'hi')
        self.assertEqual(good(l([2,3]), 'hi', 1), v2)
    
    def testMany0(self):
        val = p.literal(3).many0()
        self.assertEqual(val.parse(l([4,4,4]), {}), good(l([4,4,4]), {}, []))
        self.assertEqual(val.parse(l([3,3,4,5]), {}), good(l([4,5]), {}, [3,3]))
    
    def testMany1(self):
        val = p.literal(3).many1()
        self.assertEqual(val.parse(l([4,4,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,3,4,5]), {}), good(l([4,5]), {}, [3,3]))
    
    def testAll(self):
        val = p.all([p.item, p.literal(2), p.literal(8)])
        self.assertEqual(val.parse(l([3,2,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,2,8,16]), {}), good(l([16]), {}, [3,2,8]))
    
    def testApp(self):
        parser = p.app(lambda x,y,z: x + y * z, p.item, p.satisfy(lambda x: x > 2), p.item)
        v1 = parser.parse(l([1,2,3,4,5]), 'hi')
        self.assertEqual(m.zero, v1)
        v2 = parser.parse(l([5,6,7,8,9]), 'bye')
        self.assertEqual(good(l([8,9]), 'bye', 47), v2)
        v3 = parser.parse(l([5,6]), 'goodbye')
        self.assertEqual(m.zero, v3)
    
    def testOptional(self):
        parser = p.literal(3).optional('blargh')
        v1 = parser.parse(l([1,2,3]), 'hi')
        self.assertEqual(good(l([1,2,3]), 'hi', 'blargh'), v1)
        v2 = parser.parse(l([3,2,1]), 'bye')
        self.assertEqual(good(l([2,1]), 'bye', 3), v2)
    
    def testSeq2R(self):
        val = p.literal(2).seq2R(p.literal(3))
        self.assertEqual(val.parse(l([4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,3,4]), {}), good(l([4]), {}, 3))
    
    def testSeq2L(self):
        val = p.literal(2).seq2L(p.literal(3))
        self.assertEqual(val.parse(l([4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,3,4]), {}), good(l([4]), {}, 2))
    
    def testLookahead(self):
        parser = p.literal(2).seq2L(p.literal(3).lookahead())
        self.assertEqual(good(l([3,4,5]), None, 2), parser.parse(l([2,3,4,5]), None))
        self.assertEqual(m.zero, parser.parse(l([2,4,5]), None))
        self.assertEqual(m.zero, parser.parse(l([3,4,5]), None))
    
    def testNot0(self):
        val = p.literal(2).not0()
        self.assertEqual(val.parse(l([2,3,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,4,5]), {}), good(l([3,4,5]), {}, None))
    
    def testNot1(self):
        val = p.literal(2).not1()
        self.assertEqual(val.parse(l([2,3,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,4,5]), {}), good(l([4,5]), {}, 3))
    
    def testCommit(self):
        val = p.literal(2).commit('bag-agg')
        self.assertEqual(val.parse(l([2,3,4]), 'hi'), good(l([3,4]), 'hi', 2))
        self.assertEqual(val.parse(l([3,4,5]), 'hi'), m.error('bag-agg'))
    
    def testString(self):
        parser = p.string('abc')
        v1 = parser.parse(l('abcdef'), None)
        self.assertEqual(good(l('def'), None, 'abc'), v1)
        v2 = parser.parse(l('abdef'), None)
        self.assertEqual(m.zero, v2)
    
    def testAny(self):
        p1 = p.any([p.literal(1), p.literal(2)])
        self.assertEqual(good(l([3,4]), None, 1), p1.parse(l([1,3,4]), None))
        self.assertEqual(good(l([3,4]), None, 2), p1.parse(l([2,3,4]), None))
        self.assertEqual(m.zero, p1.parse(l([3,3,4]), None))
        p2 = p.any([p.literal(1), p.error('oops')])
        self.assertEqual(good(l([3,4]), None, 1), p2.parse(l([1,3,4]), None))
        self.assertEqual(m.error('oops'), p2.parse(l([2,3,4]), None))
    
    def testZero(self):
        self.assertEqual(m.zero, p.zero.parse(None, None))
    
    def testItem(self):
        self.assertEqual(p.item.parse(l(range(5)), {}), good(l([1,2,3,4]), {}, 0))
        
    def testGet(self):
        self.assertEqual(p.get.parse('abc', {}), good('abc', {}, 'abc'))
    
    def testGetState(self):
        self.assertEqual(good('abc', 123, 123), p.getState.parse('abc', 123))



class TestCountParser(u.TestCase):
    
    def testItem(self):
        parser = s.CountParser.item
        self.assertEqual(good(l('bcd'), (1, 2), 'a'), parser.parse(l('abcd'), (1, 1)))
        self.assertEqual(good(l('bcd'), (2, 1), '\n'), parser.parse(l('\nbcd'), (1, 1)))
    
    def testLiteral(self):
        parser = s.CountParser.literal('3').plus(s.CountParser.literal('4'))
        self.assertEqual(good(l('456'), (1, 2), '3'), parser.parse(l('3456'), (1, 1)))
        self.assertEqual(good(l('56'), (1, 2), '4'), parser.parse(l('456'), (1, 1)))
        self.assertEqual(m.zero, parser.parse(l('56'), (1, 1)))
    