from .maybeerror import MaybeError as M


class Parser(object):
    
    def __init__(self, parse):
        self.parse = parse
        

def result(value, rest, state):
    return {'result': value, 'rest': rest, 'state': state}

def good(value, rest, state):
    return M.pure(result(value, rest, state))

def compose(f, g):
    return lambda x: f(g(x))

def fmap(p, g):
    '''
    Parser e s (m t) a -> (a -> b) -> Parser e s (m t) b
    '''
    def h(r):
        return result(g(r['result']), r['rest'], r['state'])
    def f(xs, s):
        return p.parse(xs, s).fmap(h)
    return Parser(f)

def pure(x):
    '''
    a -> Parser e s (m t) a
    '''            
    def f(xs, s):
        return good(x, xs, s)
    return Parser(f)

def bind(self, g):
    '''
    Parser e s (m t) a -> (a -> Parser e s (m t) b) -> Parser e s (m t) b
    '''
    def f(xs, s):
        r = self.parse(xs, s)
        val = r.value
        if r.status == 'success':
            return g(val['result']).parse(val['rest'], val['state'])
        else:
            return r
    return Parser(f)

def plus(self, other):
    '''
    Parser e s (m t) a -> Parser e s (m t) a -> Parser e s (m t) a
    '''
    def f(xs, s):
        return self.parse(xs, s).plus(other.parse(xs, s))
    return Parser(f)

@staticmethod
def error(e):
    '''
    e -> Parser e s (m t) a
    '''
    def f(xs, s):
        return M.error(e)
    return Parser(f)

def catchError(p, f):
    '''
    Parser e s (m t) a -> (e -> Parser e s (m t) a) -> Parser e s (m t) a
    '''
    def g(xs, s):
        v = p.parse(xs, s)
        if v.status == 'error':
            return f(v.value)
        return v
    return Parser(g)

def mapError(p, f):
    '''
    Parser e s (m t) a -> (e -> e) -> Parser e s (m t) a
    '''
    return catchError(p, compose(error, f))

def put(xs):
    '''
    m t -> Parser e s (m t) a
    '''
    def f(_xs_, s):
        return good(None, xs, s)
    return Parser(f)

def putState(s):
    '''
    s -> Parser e s (m t) a
    '''
    def f(xs, _s_):
        return good(None, xs, s)
    return Parser(f)

def updateState(g):
    '''
    (s -> s) -> Parser e s (m t) a
    '''
    def f(xs, s):
        return good(None, xs, g(s))
    return Parser(f)

def check(self, predicate):
    '''
    Parser e s (m t) a -> (a -> Bool) -> Parser e s (m t) a
    '''
    def f(xs, s):
        r = self.parse(xs, s)
        if r.status != 'success':
            return r
        elif predicate(r.value['result']):
            return r
        return M.zero
    return Parser(f)

def many0(self):
    '''
    Parser e s (m t) a -> Parser e s (m t) [a]
    '''
    def f(xs, s):
        vals = []
        tokens = xs
        state = s
        while True:
            r = self.parse(tokens, state)
            if r.status == 'success':
                vals.append(r.value['result'])
                state = r.value['state']
                tokens = r.value['rest']
            elif r.status == 'failure':
                return good(vals, tokens, state)
            else:  # must respect errors
                return r
    return Parser(f)

def many1(self):
    '''
    Parser e s (m t) a -> Parser e s (m t) [a]
    '''
    return check(many0(self), lambda x: len(x) > 0)

def all_(parsers):
    '''
    [Parser e s (m t) a] -> Parser e s (m t) [a]
    '''
    def f(xs, s):
        vals = []
        state, tokens = s, xs
        for p in parsers:
            r = p.parse(tokens, state)
            if r.status == 'success':
                vals.append(r.value['result'])
                state = r.value['state']
                tokens = r.value['rest']
            else:
                return r
        return good(vals, tokens, state)
    return Parser(f)

def app(f, *parsers):
    '''
    (a -> ... y -> z) -> Parser e s (m t) a -> ... -> Parser e s (m t) y -> Parser e s (m t) z
    '''
    return fmap(all_(parsers), lambda rs: f(*rs))

def optional(self, x):
    '''
    Parser e s (m t) a -> a -> Parser e s (m t) a
    '''
    return plus(self, pure(x))

def seq2L(self, other):
    '''
    Parser e s (m t) a -> Parser e s (m t) b -> Parser e s (m t) a
    '''
    def f(x):
        return x[0]
    return fmap(all_([self, other]), f)

def seq2R(self, other):
    '''
    Parser e s (m t) a -> Parser e s (m t) b -> Parser e s (m t) b
    '''
    def g(x):
        return x[1]
    return fmap(all_([self, other]), g)

def not0(self):
    '''
    Parser e s (m t) a -> Parser e s (m t) None
    '''
    def f(xs, s):
        r = self.parse(xs, s)
        if r.status == 'error':
            return r
        elif r.status == 'success':
            return M.zero
        else:
            return good(None, xs, s)
    return Parser(f)

def commit(self, e):
    '''
    Parser e s (m t) a -> e -> Parser e s (m t) a
    '''
    return plus(self, error(e))

def any_(parsers):
    '''
    [Parser e s (m t) a] -> Parser e s (m t) a
    '''
    def f(xs, s):
        r = M.zero
        for p in parsers:
            r = p.parse(xs, s)
            if r.status in ['success', 'error']:
                return r
        return r
    return Parser(f)


def f_item(xs, s):
    if xs.isEmpty():
        return M.zero
    first, rest = xs.first(), xs.rest()
    return good(first, rest, s)

# Parser e s (m t) t
basicItem = Parser(f_item)


# Parser e s (m t) (m t)
get = Parser(lambda xs, s: good(xs, xs, s))

# Parser e s (m t) s
getState = Parser(lambda xs, s: good(s, xs, s))


def buildParsers(itemP):
    '''
    These parsers are built out of the most basic parser -- itemP -- that 
    consumes one single token if available.
    I couldn't figure out any better place to put them or thing to do with them --
    they don't seem to belong in a class, as far as I can tell.
    '''
    
    def literal(x):
        '''
        Eq t => t -> Parser e s (m t) t
        '''
        return check(itemP, lambda y: x == y)

    def satisfy(pred):
        '''
        (t -> Bool) -> Parser e s (m t) t
        '''
        return check(itemP, pred)

    def not1(self):
        '''
        Parser e s (m t) a -> Parser e s (m t) t
        '''
        return seq2R(not0(self), itemP)

    def string(elems):
        '''
        Eq t => [t] -> Parser e s (m t) [t] 
        '''
        matcher = all_(map(literal, elems))
        return seq2R(matcher, pure(elems))
    
    return (literal, satisfy, not1, string)

def bump(x):
    def action(y):
        line, col = y
        if x == '\n':
            return (line + 1, 1)
        return (line, col + 1)
    return seq2R(updateState(action), pure(x))

countingItem = bind(basicItem, bump)


standard = buildParsers(basicItem)
counting = buildParsers(countingItem)
