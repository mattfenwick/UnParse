from .. import maybeerror
import unittest as u



m = maybeerror.MaybeError

def inc(x):
    return x + 1


class Tests(u.TestCase):

    def testPure(self):
        myP = m.pure(3)
        self.assertEqual(myP.value, 3)
        self.assertEqual(myP.status, 'success')
    
    def testZero(self):
        myZ = m.zero
        self.assertEqual(myZ.value, None)
        self.assertEqual(myZ.status, 'failure')
    
    def testError(self):
        myE = m.error('hi')
        self.assertEqual(myE.value, 'hi')
        self.assertEqual(myE.status, 'error')
    
    def testEquality(self):
        self.assertEqual(m.pure(3), m.pure(3))
        self.assertEqual(m.zero, m.zero)
        self.assertEqual(m.error('hi'), m.error('hi'))
        
    def testInequality(self):
        self.assertNotEqual(m.pure(3), m.pure(4))
        self.assertNotEqual(m.pure(3), m.zero)
        self.assertNotEqual(m.pure(3), m.error(3))
        self.assertNotEqual(m.zero, m.pure(4))
        self.assertNotEqual(m.zero, m.error('hi'))
        self.assertNotEqual(m.error(3), m.pure(3))
        self.assertNotEqual(m.error('hi'), m.zero)
        self.assertNotEqual(m.error('hi'), m.error('bye'))

    def testFmap(self):
        good, bad, error = m.pure(3), m.zero, m.error('oops')
        self.assertEqual(good.fmap(inc), m.pure(4))
        self.assertEqual(bad.fmap(inc), bad)
        self.assertEqual(error.fmap(inc), error)
        self.assertEqual(good.status, 'success')
        self.assertEqual(good.value, 3)
    
    def testBind(self):
        g1, g2, g3, b, e = m.pure(1), m.pure(4), m.pure(8), m.zero, m.error('oops')
        def f(x):
            if x > 5:
                return m.pure(x + 3)
            elif 3 < x <= 5:
                return m.error('bad x: ' + str(x))
            return m.zero
        self.assertEqual(g1.bind(f), b)
        self.assertEqual(g2.bind(f), m.error('bad x: 4'))
        self.assertEqual(g3.bind(f), m.pure(11))
        self.assertEqual(b.bind(f), b)
        self.assertEqual(e.bind(f), e)
    
    def testApp(self):
        g1, g2, g3 = map(m.pure, [3, 4, 5])
        z1, e1 = m.zero, m.error('oops')
        def f(x, y, z):
            return [x, z, y, z]
        # apply over lots of success
        self.assertEqual(m.pure([3, 5, 4, 5]), m.app(f, g1, g2, g3))
        # short-circuit zero
        self.assertEqual(z1, m.app(f, g1, z1, g2))
        # short-circuit error
        self.assertEqual(e1, m.app(f, g1, g3, e1))

    def testPlus(self):
        g1, g2, bad, err = m.pure(4), m.pure('hi'), m.zero, m.error('oops')
        # good + x -> good (left-biased)
        self.assertEqual(g1.plus(g2), g1)
        self.assertEqual(g2.plus(g1), g2)
        self.assertEqual(g1.plus(bad), g1)
        self.assertEqual(g1.plus(err), g1)
        # bad + x -> x
        self.assertEqual(bad.plus(g1), g1)
        self.assertEqual(bad.plus(bad), bad)
        self.assertEqual(bad.plus(err), err)
        # error + x -> error (left-biased)
        self.assertEqual(err.plus(g1), err)
        self.assertEqual(err.plus(bad), err)
        self.assertEqual(err.plus(m.error('another error')), err)

    def testMapError(self):
        good, bad, error = m.pure(3), m.zero, m.error(4)
        self.assertEqual(good, good.mapError(inc))
        self.assertEqual(bad, bad.mapError(inc))
        self.assertEqual(m.error(5), error.mapError(inc))
