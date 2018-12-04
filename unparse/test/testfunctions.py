import unittest as u
from ..functions import (
    compose, first, second, pair, const_f, id_f,
    flipApply, reverseApplyAll, applyAll, cons,
    replicate, updatePosition)


def triple(x):
    return x * 3

def plus4(y):
    return y + 4

class Tests(u.TestCase):

    def testComposeAddThenTriple(self):
        addThenTriple = compose(triple, plus4)
        self.assertEqual(addThenTriple(8), 36)
        self.assertEqual(addThenTriple(19), 69)
    
    def testComposeTripleThenAdd(self):
        tripleThenAdd = compose(plus4, triple)
        self.assertEqual(tripleThenAdd(8), 28)
        self.assertEqual(tripleThenAdd(19), 61)
    
    def testfirst(self):
        self.assertEqual(first(1, 2), 1)
        self.assertEqual(first(2, 1), 2)
    
    def testsecond(self):
        self.assertEqual(second(1, 2), 2)
        self.assertEqual(second(2, 1), 1)
    
    def testpair(self):
        self.assertEqual(pair(1, 2), (1, 2))
    
    def testconstf(self):
        self.assertEqual(const_f("abc")(), "abc")
        self.assertEqual(const_f("abc")(1, 2, 3), "abc")
        self.assertEqual(const_f(None)(1, 2, 3), None)
    
    def testid(self):
        self.assertEqual(id_f(123), 123)
        self.assertEqual(id_f(None), None)
    
    def testcons(self):
        self.assertEqual(cons(3, ['a', 'b']), [3, 'a', 'b'])
        self.assertEqual(cons(4, []), [4])
    
    def testreplicate(self):
        self.assertEqual(replicate(0, 4), [])
        self.assertEqual(replicate(3, 4), [4, 4, 4])
    
    def testflipApply(self):
        self.assertEqual(flipApply(3, triple), 9)
    
    def testdict(self):
        self.assertEqual(dict([['b', 2], ['a', 1]]), {'a': 1, 'b': 2})
        self.assertEqual(dict([]), {})
    
    def testupdatePosition(self):
        self.assertEqual(updatePosition('\n', [3, 8]), (4, 1))
        self.assertEqual(updatePosition('\r', [3, 8]), (3, 9))
        self.assertEqual(updatePosition('\f', [3, 8]), (3, 9))
        self.assertEqual(updatePosition(' ', [3, 8]), (3, 9))
        self.assertEqual(updatePosition('t', [3, 8]), (3, 9))
    
    def testapplyAll(self):
        self.assertEqual(applyAll(3, [lambda x: x + 100, lambda y: y * 100, lambda z: z - 1]), 10299)
        self.assertEqual(applyAll("hi", []), "hi")

    def testreverseApplyAll(self):
        self.assertEqual(reverseApplyAll([lambda x: x + 100, lambda y: y * 100, lambda z: z - 1], 3), 300)
        self.assertEqual(reverseApplyAll([], "hi"), "hi")


if __name__ == "__main__":
    u.main()
