import functools


def compose(f, g):
    return lambda x: f(g(x))

def first(x, _):
    return x

def second(_, y):
    return y

def pair(x, y):
    return (x, y)

def const_f(x):
    return lambda *args: x

def id_f(x):
    return x

def cons(first, rest):
    return [first] + rest

def replicate(count, item):
    return [item for _ in range(count)]

def flipApply(x, f):
    return f(x)

def updatePosition(char, position):
    """
    only treats `\n` as newline
    """
    line, col = position
    return (line + 1, 1) if (char == '\n') else (line, col + 1)

def applyAll(x, fs):
    return functools.reduce(lambda y, g: g(y), fs, x)

def reverseApplyAll(fs, x):
    return applyAll(x, fs[::-1])
