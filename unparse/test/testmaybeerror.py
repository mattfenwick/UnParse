from .. import maybeerror
import unittest as u


m = maybeerror.MaybeError

def inc(x):
    return x + 1

def f_b(x):
    if x == 3:
        return m.pure(x + 1)
    elif x == 4:
        return m.zero
    return m.error('e1')

def f_a(x, y, z):
    return [x, z, y, z]

g1, g2, g3, g4 = map(m.pure, ['g1', 'g2', 3, 4])
e1, e2, e3, e4 = map(m.error, ['e1', 'e2', 3, 4])
b1 = m.zero


class Tests(u.TestCase):

    def testPure(self):
        self.assertEqual(g1.value, 'g1')
        self.assertEqual(g1.status, 'success')
    
    def testZero(self):
        self.assertEqual(b1.value, None)
        self.assertEqual(b1.status, 'failure')
    
    def testError(self):
        self.assertEqual(e1.value, 'e1')
        self.assertEqual(e1.status, 'error')

    def testConstructors(self):
        self.assertEqual(g1, m('success', 'g1'))
        self.assertEqual(b1, m('failure', None))
        self.assertEqual(e1, m('error', 'e1'))
    
    def testEquality(self):
        self.assertEqual(g1, g1)
        self.assertEqual(b1, b1)
        self.assertEqual(e1, e1)
        
    def testInequality(self):
        self.assertNotEqual(g1, g2)
        self.assertNotEqual(g1, b1)
        self.assertNotEqual(g1, e1)
        self.assertNotEqual(b1, g1)
        self.assertNotEqual(b1, e1)
        self.assertNotEqual(e1, g1)
        self.assertNotEqual(e1, b1)
        self.assertNotEqual(e1, e2)

    def testFmap(self):
        self.assertEqual(g3.fmap(inc), g4)
        self.assertEqual(b1.fmap(inc), b1)
        self.assertEqual(e3.fmap(inc), e3)
    
    def testBind(self):
        self.assertEqual(g2.bind(f_b), e1)
        self.assertEqual(g3.bind(f_b), g4)
        self.assertEqual(g4.bind(f_b), b1)
        self.assertEqual(b1.bind(f_b), b1)
        self.assertEqual(e1.bind(f_b), e1)
    
    def testApp(self):
        # apply over lots of success
        self.assertEqual(m.app(f_a, g1, g2, g3), m.pure(['g1', 3, 'g2', 3]))
        # short-circuit zero
        self.assertEqual(m.app(f_a, g1, b1, g2), b1)
        # short-circuit error
        self.assertEqual(m.app(f_a, g1, g3, e1), e1)

    def testPlus(self):
        # good + x -> good (left-biased)
        self.assertEqual(g1.plus(g2), g1)
        self.assertEqual(g1.plus(b1), g1)
        self.assertEqual(g1.plus(e1), g1)
        # bad + x -> x
        self.assertEqual(b1.plus(g1), g1)
        self.assertEqual(b1.plus(b1), b1)
        self.assertEqual(b1.plus(e1), e1)
        # error + x -> error (left-biased)
        self.assertEqual(e1.plus(g1), e1)
        self.assertEqual(e1.plus(b1), e1)
        self.assertEqual(e1.plus(e2), e1)

    def testMapError(self):
        self.assertEqual(g1.mapError(inc), g1)
        self.assertEqual(b1.mapError(inc), b1)
        self.assertEqual(e3.mapError(inc), e4)


if __name__ == "__main__":
    u.main()
