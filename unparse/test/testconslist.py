from .. import combinators
import unittest as u


C = combinators.ConsList

c1 = C([1,2,3,4], 0) # normal, not empty
c2 = C([], 0)        # normal, empty
c3 = C([1,2,8,4], 2) # not normal, not empty
c4 = C([1,2], 2)     # not normal, empty
c5 = C([1,2], 3)     # overindexed, empty


class TestConsList(u.TestCase):
    
    def testIsEmpty(self):
        self.assertFalse(c1.isEmpty())
        self.assertTrue(c2.isEmpty())
        self.assertFalse(c3.isEmpty())
        self.assertTrue(c4.isEmpty())
        self.assertTrue(c5.isEmpty())
    
    def testFirst(self):
        self.assertEqual(1, c1.first())
        self.assertEqual(8, c3.first())
        for c in (c2, c4, c5):
            try:
                self.assertEqual(c.first(), 'cannot get first of empty sequence')
            except ValueError as e:
                self.assertEqual('cannot get first element of empty sequence', e.message)

    def testRest(self):
        self.assertEqual(C([2,3,4], 0), c1.rest())
        self.assertEqual(C([4], 0), c3.rest())
        for c in (c2, c4, c5):
            try:
                self.assertEqual(c.rest(), 'cannot get rest of empty sequence')
            except ValueError as e:
                self.assertEqual('cannot get rest of empty sequence', e.message)
    
    def testGetAsList(self):
        self.assertEqual([1,2,3,4], c1.getAsList())
        self.assertEqual([], c2.getAsList())
        self.assertEqual([8,4], c3.getAsList())
        self.assertEqual([], c4.getAsList())
        self.assertEqual([], c5.getAsList())
    
    def testEquality(self):
        self.assertEqual(C([1,2,3], 0), C([0,1,2,3], 1))
        self.assertEqual(C([0,1,2,3], 1), C([1,2,3], 0))
        self.assertEqual(C([2,3,4,5,6], 4), C([6], 0))
        self.assertEqual(C([6], 0), C([2,3,4,5,6], 4))
        # elements before the start aren't "in" the sequence
        self.assertEqual(C([5,2,3], 1), C([4,2,3], 1))
    
    def testInequality(self):
        self.assertNotEqual(C([1,2,3], 0), C([1,2,3], 1))
        self.assertNotEqual(C([1,2,3], 1), C([1,2,3], 0))
        self.assertNotEqual(C([1,2,3], 1), C([1,4,3], 1))
        self.assertNotEqual(C([1,4,3], 1), C([1,2,3], 1))
