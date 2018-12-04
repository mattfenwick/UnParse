'''
@author: matt
'''
from ..cst import (cut, addErrorState, node)
from ..combinators import (ConsList, run, basic, zero, error, count, good)
from ..maybeerror import MaybeError
import unittest as u


C = ConsList
err = MaybeError.error
iz1 = basic

def cstnode(name, start, end, **kwargs):
    kwargs['_name'] = name
    kwargs['_start'] = start
    kwargs['_end'] = end
    return kwargs


class TestCst(u.TestCase):
    
    def testCutSuccess(self):
        self.assertEqual(cut('oops', basic.item).parse(C('abc'), None), good('a', C('bc'), None))
        self.assertEqual(cut('oops', zero).parse(C('abc'), 12), err([('oops',12)]))
        self.assertEqual(cut('oops', error('err')).parse(C('abc'), 12), err('err'))

    def testAddErrorState(self):
        self.assertEqual(addErrorState('oops', iz1.item).parse(C('abc'), None),
                         good('a', C('bc'), None))
        self.assertEqual(addErrorState('oops', zero).parse(C('abc'), 12),
                         MaybeError.zero)
        self.assertEqual(addErrorState('oops', error(['err'])).parse(C('abc'), 12),
                         MaybeError.error([('oops', 12), 'err']))
    
    def testNodeSuccess(self):
        self.assertEqual(node('blar').parse(C('abc'), 17), 
                         good(cstnode('blar', 17, 17), C('abc'), 17))
        self.assertEqual(node('blar', ('a', count.item)).parse(C('def'), 17), 
                         good(cstnode('blar', 17, 18, a='d'), C('ef'), 18))
        self.assertEqual(node('blar', ('a', count.item), ('b', count.item)).parse(C('def'), 17), 
                         good(cstnode('blar', 17, 19, a='d', b='e'), C('f'), 19))
    
    def testNodeFailure(self):
        self.assertEqual(node('blar', ('a', zero)).parse(C('abc'), 17),
                         MaybeError.zero)
    
    def testNodeError(self):
        self.assertEqual(node('blar', ('a', cut('oops', zero))).parse(C('abc'), 17), 
                         err([('blar', 17), ('oops', 17)]))
        self.assertEqual(node('blar', ('a', count.item), ('b', cut('oops', zero))).parse(C('def'), 17), 
                         err([('blar', 17), ('oops', 18)]))


if __name__ == "__main__":
    u.main()
