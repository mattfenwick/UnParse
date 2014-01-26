'''
@author: matt
'''
import cProfile
import pstats
from .maybeerror import MaybeError
from . import combinators as c
from .combinators import (good, run, Itemizer, basic, position, count, Parser, many0,
                          seq2R, bind, zero, put, pure, get, seq2L, updateState)


def profile(f, *args, **kwargs):
    cProfile.runctx('f(*args, **kwargs)', {}, {'f': f, 'args': args, 'kwargs': kwargs}, 'prof.txt')
    stats = pstats.Stats('prof.txt')
    stats.sort_stats('time').print_stats()
    return stats


def _action(xs):
    if xs.isEmpty():
        return zero
    return seq2R(put(xs.rest()), pure(xs.first()))

_item = bind(get, _action)

bas = Itemizer(_item)
pos = Itemizer(bind(basic.item, 
                    lambda char: seq2R(updateState(lambda s: c._bump(char, s)), pure(char))))
ct = Itemizer(seq2L(basic.item, updateState(lambda x: x + 1)))

def random_nums(size=100000):
    nums = []
    import random
    for _ in xrange(size):
        nums.append(random.randint(0, 10000))
    return nums

def test_case(p1, p2, size=100000, state=None):
    nums = random_nums(size)
    a = profile(run, many0(p1), nums, state)
    b = profile(run, many0(p2), nums, state)
    return a, b

def test_basic(size):
    return test_case(basic.item, bas.item, size)

def test_pos(size):
#    return test_case(position.item, pos.item, size)
    return test_case(pos.item, position.item, size, (1,1))

def test_count(size):
    return test_case(ct.item, count.item, size, 1)

def test_all(size):
    return [f(size) for f in [test_basic, test_pos, test_count]]

print run(position.item, 'abc')
print run(many0(pos.item), range(8))
