from .. import combinators as c
from .. import maybeerror as me
import unittest as u


m = me.MaybeError

l = c.ConsList

def good(rest, state, result):
    return m.pure({'rest': rest, 'state': state, 'result': result})

iz1 = c.basic
(item1, lit1, sat1, not11, str1) = iz1.item, iz1.literal, iz1.satisfy, iz1.not1, iz1.string
iz2 = c.position
(item2, lit2, sat2, not12, str2) = iz2.item, iz2.literal, iz2.satisfy, iz2.not1, iz2.string



class BasicTokens(u.TestCase):

    def testItemBasic(self):
        self.assertEqual(m.zero, item1.parse(l(''), None))
        self.assertEqual(good(l('bcdef'), None, 'a'), item1.parse(l('abcdef'), None))

    def testLiteral(self):
        val = lit1(3)
        self.assertEqual(val.parse(l([3,4,5]), {}), good(l([4,5]), {}, 3))
        self.assertEqual(val.parse(l([4,5]), {}), m.zero)
    
    def testSatisfy(self):
        v1 = sat1(lambda x: x > 3).parse(l([1,2,3]), 'bye')
        self.assertEqual(m.zero, v1)
        v2 = sat1(lambda x: x < 3).parse(l([1,2,3]), 'hi')
        self.assertEqual(good(l([2,3]), 'hi', 1), v2)
    
    def testString(self):
        parser = str1('abc')
        v1 = parser.parse(l('abcdef'), None)
        self.assertEqual(good(l('def'), None, 'abc'), v1)
        v2 = parser.parse(l('abdef'), None)
        self.assertEqual(m.zero, v2)
    
    def testNot1(self):
        val = not11(lit1(2))
        self.assertEqual(val.parse(l([2,3,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,4,5]), {}), good(l([4,5]), {}, 3))






class CountTokens(u.TestCase):

    def testItemPosition(self):
        self.assertEqual(m.zero, item2.parse(l(''), (1,1)))
        self.assertEqual(good(l('bcdef'), (1,2), 'a'), item2.parse(l('abcdef'), (1,1)))
        self.assertEqual(good(l('bcdef'), (2,1), '\n'), item2.parse(l('\nbcdef'), (1,1)))

    def testLiteral(self):
        val = lit2('3')
        self.assertEqual(val.parse(l('345'), (3,8)), good(l('45'), (3,9), '3'))
        self.assertEqual(val.parse(l('45'), (3,8)), m.zero)
    
    def testSatisfy(self):
        v1 = sat2(lambda x: int(x) > 3).parse(l('123'), (2,2))
        self.assertEqual(m.zero, v1)
        v2 = sat2(lambda x: int(x) < 3).parse(l('123'), (2,2))
        self.assertEqual(good(l('23'), (2,3), '1'), v2)
    
    def testString(self):
        parser = str2('abc')
        v1 = parser.parse(l('abcdef'), (4,3))
        self.assertEqual(good(l('def'), (4,6), 'abc'), v1)
        v2 = parser.parse(l('abdef'), (4,3))
        self.assertEqual(m.zero, v2)
    
    def testNot1(self):
        val = not12(lit2('2'))
        self.assertEqual(val.parse(l('234'), (1,1)), m.zero)
        self.assertEqual(val.parse(l('345'), (1,1)), good(l('45'), (1,2), '3'))


    
class TestParser(u.TestCase):
    
    def testFmap(self):
        f = lambda x: x + 7
        v1 = c.fmap(f, c.pure(3)).parse('ab', 81)
        self.assertEqual(good('ab', 81, 10), v1)
        v2 = c.fmap(f, c.zero).parse('ab', 81)
        self.assertEqual(m.zero, v2)
        v3 = c.fmap(f, c.error('oops')).parse('ab', 81)
        self.assertEqual(m.error('oops'), v3)
        
    def testPure(self):
        val = c.pure(3).parse('abc', 2)
        self.assertEqual(good('abc', 2, 3), val)
    
    def testBind(self):
        two = c.bind(item1, lambda x: lit1(x))
        self.assertEqual(two.parse(l('abcde'), {}), m.zero)
        self.assertEqual(two.parse(l('aabcde'), {}), good(l('bcde'), {}, 'a'))

    def testPlus(self):
        g1, g2, b, e, e2 = c.pure(3), c.pure('hi'), c.zero, c.error('oops'), c.error('2nd')
        r1, r3, r4 = good('abc', None, 3), m.zero, m.error('oops')
        self.assertEqual(c.plus(g1, g2).parse('abc', None), r1)
        self.assertEqual(c.plus(g1, b).parse('abc', None), r1)
        self.assertEqual(c.plus(g1, e).parse('abc', None), r1)
        self.assertEqual(c.plus(b, g1).parse('abc', None), r1)
        self.assertEqual(c.plus(b, b).parse('abc', None), r3)
        self.assertEqual(c.plus(b, e).parse('abc', None), r4)
        self.assertEqual(c.plus(e, g1).parse('abc', None), r4)
        self.assertEqual(c.plus(e, b).parse('abc', None), r4)
        self.assertEqual(c.plus(e, e2).parse('abc', None), r4)
    
    def testError(self):
        v1 = c.error('uh-oh').parse('abc', 123)
        self.assertEqual(m.error('uh-oh'), v1)
    
    def testCatchError(self):
        f1 = lambda e: c.pure(3)
        f2 = lambda e: c.error('dead again')
        # error -> good -- resumes parsing with tokens and state from before the error occurred
        self.assertEqual(good('123', [2,4], 3), c.catchError(f1, c.error('dead 1')).parse('123', [2, 4]))
        # good -> good (unaffected by this combinator)
        self.assertEqual(good('123', [2,4], 18), c.catchError(f1, c.pure(18)).parse('123', [2,4]))
        # error -> error
        self.assertEqual(m.error('dead again'), c.catchError(f2, c.error('dead 1')).parse('123', [2,4]))
        # good -> error is not possible with this combinator
        
    def testMapError(self):
        f = len
        v1 = c.mapError(f, c.error('abcdef')).parse('123abc', None)
        self.assertEqual(m.error(6), v1)
        v2 = c.mapError(f, c.zero).parse('123abc', None)
        self.assertEqual(m.zero, v2)
        v3 = c.mapError(f, c.pure(82)).parse('123abc', None)
        self.assertEqual(good('123abc', None, 82), v3)        

    def testPut(self):
        val = c.put('xyz')
        self.assertEqual(val.parse('abc', []), good('xyz', [], None))
    
    def testPutState(self):
        v1 = c.putState(29).parse('abc123', 2)
        self.assertEqual(good('abc123', 29, None), v1)
    
    def testUpdateState(self):
        v1 = c.updateState(lambda x: x * 4).parse('abc', 18)
        self.assertEqual(good('abc', 72, None), v1)
        
    def testCheck(self):
        val = c.check(lambda x: len(x) > 3, c.get)
        self.assertEqual(val.parse('abcde', []), good('abcde', [], 'abcde'))
        self.assertEqual(val.parse('abc', []), m.zero)
    
    def testMany0(self):
        val = c.many0(lit1(3))
        self.assertEqual(val.parse(l([4,4,4]), {}), good(l([4,4,4]), {}, []))
        self.assertEqual(val.parse(l([3,3,4,5]), {}), good(l([4,5]), {}, [3,3]))
    
    def testMany1(self):
        val = c.many1(lit1(3))
        self.assertEqual(val.parse(l([4,4,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,3,4,5]), {}), good(l([4,5]), {}, [3,3]))
    
    def testAll(self):
        val = c.all_([item1, lit1(2), lit1(8)])
        self.assertEqual(val.parse(l([3,2,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,2,8,16]), {}), good(l([16]), {}, [3,2,8]))
    
    def testApp(self):
        parser = c.app(lambda x,y,z: x + y * z, item1, sat1(lambda x: x > 2), item1)
        v1 = parser.parse(l([1,2,3,4,5]), 'hi')
        self.assertEqual(m.zero, v1)
        v2 = parser.parse(l([5,6,7,8,9]), 'bye')
        self.assertEqual(good(l([8,9]), 'bye', 47), v2)
        v3 = parser.parse(l([5,6]), 'goodbye')
        self.assertEqual(m.zero, v3)
    
    def testOptional(self):
        parser = c.optional('blargh', lit1(3))
        v1 = parser.parse(l([1,2,3]), 'hi')
        self.assertEqual(good(l([1,2,3]), 'hi', 'blargh'), v1)
        v2 = parser.parse(l([3,2,1]), 'bye')
        self.assertEqual(good(l([2,1]), 'bye', 3), v2)
    
    def testSeq2R(self):
        val = c.seq2R(lit1(2), lit1(3))
        self.assertEqual(val.parse(l([4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,3,4]), {}), good(l([4]), {}, 3))
    
    def testSeq2L(self):
        val = c.seq2L(lit1(2), lit1(3))
        self.assertEqual(val.parse(l([4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,3,4]), {}), good(l([4]), {}, 2))
    
    def testLookahead(self):
        parser = c.seq2L(lit1(2), c.lookahead(lit1(3)))
        self.assertEqual(good(l([3,4,5]), None, 2), parser.parse(l([2,3,4,5]), None))
        self.assertEqual(m.zero, parser.parse(l([2,4,5]), None))
        self.assertEqual(m.zero, parser.parse(l([3,4,5]), None))
    
    def testNot0(self):
        val = c.not0(lit1(2))
        self.assertEqual(val.parse(l([2,3,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,4,5]), {}), good(l([3,4,5]), {}, None))
    
    def testCommit(self):
        val = c.commit('bag-agg', lit1(2))
        self.assertEqual(val.parse(l([2,3,4]), 'hi'), good(l([3,4]), 'hi', 2))
        self.assertEqual(val.parse(l([3,4,5]), 'hi'), m.error('bag-agg'))
    
    def testAny(self):
        p1 = c.any_([lit1(1), lit1(2)])
        self.assertEqual(good(l([3,4]), None, 1), p1.parse(l([1,3,4]), None))
        self.assertEqual(good(l([3,4]), None, 2), p1.parse(l([2,3,4]), None))
        self.assertEqual(m.zero, p1.parse(l([3,3,4]), None))
        p2 = c.any_([lit1(1), c.error('oops')])
        self.assertEqual(good(l([3,4]), None, 1), p2.parse(l([1,3,4]), None))
        self.assertEqual(m.error('oops'), p2.parse(l([2,3,4]), None))
    
    def testZero(self):
        self.assertEqual(m.zero, c.zero.parse(None, None))
    
    def testGet(self):
        self.assertEqual(c.get.parse('abc', {}), good('abc', {}, 'abc'))
    
    def testGetState(self):
        self.assertEqual(good('abc', 123, 123), c.getState.parse('abc', 123))
