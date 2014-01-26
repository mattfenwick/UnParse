from .. import combinators as c
from .. import maybeerror as me
import unittest as u


m = me.MaybeError

l = c.ConsList

def good(rest, state, result):
    return m.pure({'rest': rest, 'state': state, 'result': result})

iz1 = c.basic
iz2 = c.position
iz3 = c.count


class BasicTokens(u.TestCase):

    def testItemBasic(self):
        self.assertEqual(iz1.item.parse(l(''), None), m.zero)
        self.assertEqual(iz1.item.parse(l('abcdef'), None), good(l('bcdef'), None, 'a'))

    def testLiteral(self):
        val = iz1.literal(3)
        self.assertEqual(val.parse(l([3,4,5]), {}), good(l([4,5]), {}, 3))
        self.assertEqual(val.parse(l([4,5]), {}), m.zero)
    
    def testSatisfy(self):
        v1 = iz1.satisfy(lambda x: x > 3).parse(l([1,2,3]), 'bye')
        v2 = iz1.satisfy(lambda x: x < 3).parse(l([1,2,3]), 'hi')
        self.assertEqual(v1, m.zero)
        self.assertEqual(v2, good(l([2,3]), 'hi', 1))
    
    def testString(self):
        parser = iz1.string('abc')
        v1 = parser.parse(l('abcdef'), None)
        v2 = parser.parse(l('abdef'), None)
        self.assertEqual(v1, good(l('def'), None, 'abc'))
        self.assertEqual(v2, m.zero)
    
    def testNot1(self):
        val = iz1.not1(iz1.literal(2))
        self.assertEqual(val.parse(l([2,3,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,4,5]), {}), good(l([4,5]), {}, 3))
    
    def testOneOf(self):
        p = iz1.oneOf('abc')
        self.assertEqual(p.parse(l('cqrs'), None), good(l('qrs'), None, 'c'))
        self.assertEqual(p.parse(l('aqrs'), None), good(l('qrs'), None, 'a'))
        self.assertEqual(p.parse(l('dqrs'), None), m.zero)


class PositionTokens(u.TestCase):

    def testItemPosition(self):
        self.assertEqual(iz2.item.parse(l(''), (1,1)), m.zero)
        self.assertEqual(iz2.item.parse(l('abcdef'), (1,1)), good(l('bcdef'), (1,2), 'a'))
        self.assertEqual(iz2.item.parse(l('\nbcdef'), (1,1)), good(l('bcdef'), (2,1), '\n'))

    def testLiteral(self):
        val = iz2.literal('3')
        self.assertEqual(val.parse(l('345'), (3,8)), good(l('45'), (3,9), '3'))
        self.assertEqual(val.parse(l('45'), (3,8)), m.zero)
    
    def testSatisfy(self):
        v1 = iz2.satisfy(lambda x: int(x) > 3).parse(l('123'), (2,2))
        v2 = iz2.satisfy(lambda x: int(x) < 3).parse(l('123'), (2,2))
        self.assertEqual(v1, m.zero)
        self.assertEqual(v2, good(l('23'), (2,3), '1'))
    
    def testString(self):
        parser = iz2.string('abc')
        v1 = parser.parse(l('abcdef'), (4,3))
        v2 = parser.parse(l('abdef'), (4,3))
        self.assertEqual(v1, good(l('def'), (4,6), 'abc'))
        self.assertEqual(v2, m.zero)
    
    def testNot1(self):
        val = iz2.not1(iz2.literal('2'))
        self.assertEqual(val.parse(l('234'), (1,1)), m.zero)
        self.assertEqual(val.parse(l('345'), (1,1)), good(l('45'), (1,2), '3'))
    
    def testOneOf(self):
        p = iz2.oneOf('abc')
        self.assertEqual(p.parse(l('cqrs'), (3,4)), good(l('qrs'), (3,5), 'c'))
        self.assertEqual(p.parse(l('aqrs'), (8,1)), good(l('qrs'), (8,2), 'a'))
        self.assertEqual(p.parse(l('dqrs'), (2,2)), m.zero)


class CountTokens(u.TestCase):

    def testItemPosition(self):
        self.assertEqual(iz3.item.parse(l(''), 8), m.zero)
        self.assertEqual(iz3.item.parse(l('abcdef'), 5), good(l('bcdef'), 6, 'a'))
        self.assertEqual(iz3.item.parse(l('\nbcdef'), 100), good(l('bcdef'), 101, '\n'))

    def testLiteral(self):
        val = iz3.literal('3')
        self.assertEqual(val.parse(l('345'), 8), good(l('45'), 9, '3'))
        self.assertEqual(val.parse(l('45'), 8), m.zero)
    
    def testSatisfy(self):
        v1 = iz3.satisfy(lambda x: int(x) > 3).parse(l('123'), 22)
        v2 = iz3.satisfy(lambda x: int(x) < 3).parse(l('123'), 22)
        self.assertEqual(v1, m.zero)
        self.assertEqual(v2, good(l('23'), 23, '1'))
    
    def testString(self):
        parser = iz3.string('abc')
        v1 = parser.parse(l('abcdef'), 43)
        v2 = parser.parse(l('abdef'), 43)
        self.assertEqual(v1, good(l('def'), 46, 'abc'))
        self.assertEqual(v2, m.zero)
    
    def testNot1(self):
        val = iz3.not1(iz3.literal('2'))
        self.assertEqual(val.parse(l('234'), 61), m.zero)
        self.assertEqual(val.parse(l('345'), 61), good(l('45'), 62, '3'))
    
    def testOneOf(self):
        p = iz3.oneOf('abc')
        self.assertEqual(p.parse(l('cqrs'), 4), good(l('qrs'), 5, 'c'))
        self.assertEqual(p.parse(l('aqrs'), 8), good(l('qrs'), 9, 'a'))
        self.assertEqual(p.parse(l('dqrs'), 7), m.zero)


class TestParser(u.TestCase):
    
    def testFmap(self):
        f = lambda x: x + 7
        v1 = c.fmap(f, c.pure(3)).parse('ab', 81)
        v2 = c.fmap(f, c.zero).parse('ab', 81)
        v3 = c.fmap(f, c.error('oops')).parse('ab', 81)
        self.assertEqual(v1, good('ab', 81, 10))
        self.assertEqual(v2, m.zero)
        self.assertEqual(v3, m.error('oops'))
        
    def testPure(self):
        val = c.pure(3).parse('abc', 2)
        self.assertEqual(val, good('abc', 2, 3))
    
    def testBind(self):
        two = c.bind(iz1.item, iz1.literal)
        self.assertEqual(two.parse(l('abcde'), {}), m.zero)
        self.assertEqual(two.parse(l('aabcde'), {}), good(l('bcde'), {}, 'a'))

    def testAltBinaryRules(self):
        g1, g2, b, e, e2 = c.pure(3), c.pure('hi'), c.zero, c.error('oops'), c.error('2nd')
        r1, r3, r4 = good('abc', None, 3), m.zero, m.error('oops')
        self.assertEqual(c.alt(g1, g2).parse('abc', None), r1)
        self.assertEqual(c.alt(g1, b).parse('abc', None), r1)
        self.assertEqual(c.alt(g1, e).parse('abc', None), r1)
        self.assertEqual(c.alt(b, g1).parse('abc', None), r1)
        self.assertEqual(c.alt(b, b).parse('abc', None), r3)
        self.assertEqual(c.alt(b, e).parse('abc', None), r4)
        self.assertEqual(c.alt(e, g1).parse('abc', None), r4)
        self.assertEqual(c.alt(e, b).parse('abc', None), r4)
        self.assertEqual(c.alt(e, e2).parse('abc', None), r4)
    
    def testAltCornerCases(self):
        self.assertEqual(c.alt().parse(l([1,2,3]), None), 
                         m.zero)
        self.assertEqual(c.alt(c.pure('h')).parse(l([1,2,3]), None), 
                         good(l([1,2,3]), None, 'h'))
        self.assertEqual(c.alt(c.error('oops')).parse(l([1,2,3]), None),
                         m.error('oops'))
        self.assertEqual(c.alt(c.zero).parse(l([1,2,3]), None),
                         m.zero)
        p1 = c.alt(c.zero, iz1.literal(1), iz1.literal(2), c.error('d'))
        self.assertEqual(p1.parse(l([1,3,4]), None), good(l([3,4]), None, 1))
        self.assertEqual(p1.parse(l([2,3,4]), None), good(l([3,4]), None, 2))
        self.assertEqual(p1.parse(l([3,3,4]), None), m.error('d'))
    
    def testError(self):
        v1 = c.error('uh-oh').parse('abc', 123)
        self.assertEqual(v1, m.error('uh-oh'))
    
    def testCatchError(self):
        f1 = lambda e: c.pure(3)
        f2 = lambda e: c.error('dead again')
        # error -> good -- resumes parsing with tokens and state from before the error occurred
        self.assertEqual(c.catchError(f1, c.error('dead 1')).parse('123', [2, 4]),
                         good('123', [2,4], 3))
        # good -> good (unaffected by this combinator)
        self.assertEqual(c.catchError(f1, c.pure(18)).parse('123', [2,4]),
                         good('123', [2,4], 18))
        # error -> error
        self.assertEqual(c.catchError(f2, c.error('dead 1')).parse('123', [2,4]),
                         m.error('dead again'))
        # good -> error is not possible with this combinator
        
    def testMapError(self):
        f = len
        v1 = c.mapError(f, c.error('abcdef')).parse('123abc', None)
        v2 = c.mapError(f, c.zero).parse('123abc', None)
        v3 = c.mapError(f, c.pure(82)).parse('123abc', None)
        self.assertEqual(v1, m.error(6))
        self.assertEqual(v2, m.zero)
        self.assertEqual(v3, good('123abc', None, 82))

    def testPut(self):
        val = c.put('xyz')
        self.assertEqual(val.parse('abc', []), good('xyz', [], None))
    
    def testPutState(self):
        v1 = c.putState(29).parse('abc123', 2)
        self.assertEqual(v1, good('abc123', 29, None))
    
    def testUpdateState(self):
        v1 = c.updateState(lambda x: x * 4).parse('abc', 18)
        self.assertEqual(v1, good('abc', 72, None))
        
    def testCheck(self):
        val = c.check(lambda x: len(x) > 3, c.get)
        self.assertEqual(val.parse('abcde', []), good('abcde', [], 'abcde'))
        self.assertEqual(val.parse('abc', []), m.zero)
    
    def testMany0(self):
        val = c.many0(iz1.literal(3))
        self.assertEqual(val.parse(l([4,4,4]), {}), good(l([4,4,4]), {}, []))
        self.assertEqual(val.parse(l([3,3,4,5]), {}), good(l([4,5]), {}, [3,3]))
    
    def testMany1(self):
        val = c.many1(iz1.literal(3))
        self.assertEqual(val.parse(l([4,4,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,3,4,5]), {}), good(l([4,5]), {}, [3,3]))
    
    def testSeq(self):
        val = c.seq(iz1.item, iz1.literal(2), iz1.literal(8))
        self.assertEqual(val.parse(l([3,2,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,2,8,16]), {}), good(l([16]), {}, [3,2,8]))
    
    def testApp(self):
        parser = c.app(lambda x,y,z: x + y * z,
                       iz1.item,
                       iz1.satisfy(lambda x: x > 2),
                       iz1.item)
        v1 = parser.parse(l([1,2,3,4,5]), 'hi')
        v2 = parser.parse(l([5,6,7,8,9]), 'bye')
        v3 = parser.parse(l([5,6]), 'goodbye')
        self.assertEqual(v1, m.zero)
        self.assertEqual(v2, good(l([8,9]), 'bye', 47))
        self.assertEqual(v3, m.zero)
    
    def testOptional(self):
        parser = c.optional(iz1.literal(3), 'blargh')
        v1 = parser.parse(l([1,2,3]), 'hi')
        v2 = parser.parse(l([3,2,1]), 'bye')
        self.assertEqual(v1, good(l([1,2,3]), 'hi', 'blargh'))
        self.assertEqual(v2, good(l([2,1]), 'bye', 3))
    
    def testOptionalNoValue(self):
        p = c.optional(iz1.literal(3))
        v1 = p.parse(l([3,2,1]), None)
        v2 = p.parse(l([1,2,3]), None)
        self.assertEqual(v1, good(l([2,1]), None, 3))
        self.assertEqual(v2, good(l([1,2,3]), None, None))
    
    def testSeq2R(self):
        val = c.seq2R(iz1.literal(2), iz1.literal(3))
        self.assertEqual(val.parse(l([4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,3,4]), {}), good(l([4]), {}, 3))
    
    def testSeq2L(self):
        val = c.seq2L(iz1.literal(2), iz1.literal(3))
        self.assertEqual(val.parse(l([4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,4,5]), {}), m.zero)
        self.assertEqual(val.parse(l([2,3,4]), {}), good(l([4]), {}, 2))
    
    def testLookahead(self):
        parser = c.seq2L(iz1.literal(2), c.lookahead(iz1.literal(3)))
        self.assertEqual(parser.parse(l([2,3,4,5]), None), good(l([3,4,5]), None, 2))
        self.assertEqual(parser.parse(l([2,4,5]), None), m.zero)
        self.assertEqual(parser.parse(l([3,4,5]), None), m.zero)
    
    def testNot0(self):
        val = c.not0(iz1.literal(2))
        self.assertEqual(val.parse(l([2,3,4]), {}), m.zero)
        self.assertEqual(val.parse(l([3,4,5]), {}), good(l([3,4,5]), {}, None))
    
    def testCommit(self):
        val = c.commit('bag-agg', iz1.literal(2))
        self.assertEqual(val.parse(l([2,3,4]), 'hi'), good(l([3,4]), 'hi', 2))
        self.assertEqual(val.parse(l([3,4,5]), 'hi'), m.error('bag-agg'))
    
    def testZero(self):
        self.assertEqual(c.zero.parse(None, None), m.zero)
    
    def testGet(self):
        self.assertEqual(c.get.parse('abc', {}), good('abc', {}, 'abc'))
    
    def testGetState(self):
        self.assertEqual(c.getState.parse('abc', 123), good('abc', 123, 123))
