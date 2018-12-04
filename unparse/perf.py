'''
@author: matt
'''
from __future__ import print_function
import cProfile
import pstats
from .maybeerror import MaybeError
from .combinators import (run, many0, basic, count, position)



def profile(f, *args, **kwargs):
    cProfile.runctx('f(*args, **kwargs)', {}, {'f': f, 'args': args, 'kwargs': kwargs}, 'prof.txt')
    stats = pstats.Stats('prof.txt')
    stats.sort_stats('time').print_stats()
    return stats


def random_nums(size=100000):
    nums = []
    import random
    for _ in xrange(size):
        nums.append(random.randint(0, 10000))
    return nums

def test_case(p1, p2, size=100000, state1=None, state2=None):
    nums = random_nums(size)
    a = profile(run, many0(p1), nums, state1)
    b = profile(run, many0(p2), nums, state2)
    return a, b

def test_basic_position(size):
    return test_case(basic.item, position.item, size, None, (1,1))

def test_basic_count(size):
    return test_case(basic.item, count.item, size, None, 1)

def test_count_position(size):
    return test_case(count.item, position.item, size, 1, (1,1))

def test_all(size):
    return [f(size) for f in [test_basic_position, test_basic_count, test_count_position]]


if __name__ == "__main__":
#    print(run(position.item, 'abc'))
#    print(run(many0(position.item), range(8)))
#    for i in range(10):
#        print(test_all(2 ** i))
    print(test_all(1000000))
