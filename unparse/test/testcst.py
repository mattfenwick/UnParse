'''
@author: matt
'''
from ..cst import (cut, addError, node)
from ..combinators import (ConsList, run, basic, zero, error, count)
from ..maybeerror import MaybeError
import unittest as u


C = ConsList
err = MaybeError.error

def good(rest, state, result):
    return MaybeError.pure({
        'rest': rest,
        'state': state,
        'result': result
    })

def cstnode(name, state, **kwargs):
    kwargs['_name'] = name
    kwargs['_state'] = state
    return kwargs


class TestCst(u.TestCase):
    
    def testCutSuccess(self):
        self.assertEqual(cut('oops', basic.item).parse(C('abc'), None), good(C('bc'), None, 'a'))
    
    def testCutFail(self):
        self.assertEqual(cut('oops', zero).parse(C('abc'), 12), err([('oops',12)]))
    
    def testCutError(self):
        self.assertEqual(cut('oops', error('err')).parse(C('abc'), 12), err('err'))
    
    def testAddErrorSuccess(self):
        self.assertEqual(addError('oops', basic.item).parse(C('abc'), None), 
                         good(C('bc'), None, 'a'))

    def testAddErrorFail(self):
        self.assertEqual(addError('oops', zero).parse(C('abc'), 12), 
                         MaybeError.zero)

    def testAddErrorError(self):
        self.assertEqual(addError('oops', error(['err'])).parse(C('abc'), 12), 
                         err([('oops', 12), 'err']))

    def testNodeSuccess(self):
        self.assertEqual(node('blar').parse(C('abc'), 17), 
                         good(C('abc'), 17, cstnode('blar', 17)))
        self.assertEqual(node('blar', ('a', count.item)).parse(C('def'), 17), 
                         good(C('ef'), 18, cstnode('blar', 17, a='d')))
        self.assertEqual(node('blar', ('a', count.item), ('b', count.item)).parse(C('def'), 17), 
                         good(C('f'), 19, cstnode('blar', 17, a='d', b='e')))
    
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
