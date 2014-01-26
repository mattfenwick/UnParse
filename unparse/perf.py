'''
@author: matt
'''
import cProfile
import pstats
from .maybeerror import MaybeError
from .combinators import (good, run, Itemizer, basic, position, count, Parser, many0,
                          seq2R, bind, zero, put, pure, get)


def profile(f, *args, **kwargs):
    cProfile.runctx('f(*args, **kwargs)', {}, {'f': f, 'args': args, 'kwargs': kwargs}, 'prof.txt')
    stats = pstats.Stats('prof.txt')
    stats.sort_stats('time').print_stats()
    return stats


def _bump(c, p):
    line, col = p
    if c == '\n':
        return (line + 1, 1)
    return (line, col + 1)

def _item_position(xs, position):
    '''
    Does two things:
     - consumes a single token if available, failing otherwise (see `_item_basic`)
     - updates the position info in state -- `\n` is a newline
     
    This assumes that the state is a 2-tuple of integers, (line, column).
    '''
    if xs.isEmpty():
        return MaybeError.zero
    first, rest = xs.first(), xs.rest()
    return good(first, rest, _bump(first, position))

def _item_count(xs, ct):
    '''
    Does two things:
      1. see `_item_basic`
      2. increments a counter -- which tells how many tokens have been consumed
    '''
    if xs.isEmpty():
        return MaybeError.zero
    first, rest = xs.first(), xs.rest()
    return good(first, rest, ct + 1)

def _action(xs):
    if xs.isEmpty():
        return zero
    return seq2R(put(xs.rest()), pure(xs.first()))

_item = bind(get, _action)

bas = Itemizer(_item)
pos = Itemizer(Parser(_item_position))
ct = Itemizer(Parser(_item_count))

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


print run(position.item, 'abc')
print run(many0(pos.item), range(8))
