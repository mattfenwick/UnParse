from .maybeerror import MaybeError as M
from . import functions



class ConsList(object):
    '''
    A data structure that supports constant-time first/rest slicing.
    The input sequence is never copied or modified -- all the slicing
    does is increment a position counter and create a new wrapper.
    '''

    def __init__(self, seq, start=0):
        self.seq = seq
        self.start = start
        
    def isEmpty(self):
        return self.start >= len(self.seq)
        
    def first(self):
        '''
        Returns first element.  Throws exception if empty.
        '''
        if not self.isEmpty():
            return self.seq[self.start]
        raise ValueError('cannot get first element of empty sequence')
        
    def rest(self):
        '''
        Return ConsList of all but the first element.
        Throws exception if empty.
        '''
        if not self.isEmpty():
            return ConsList(self.seq, self.start + 1)
        raise ValueError('cannot get rest of empty sequence')
    
    def getAsList(self):
        '''
        Return list of remaining elements.
        '''
        return list(self.seq[self.start:])
        
    def __eq__(self, other):
        try:
            return self.getAsList() == other.getAsList()
        except:
            return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
        
    def __repr__(self):
        return repr({
            'type': 'cons list', 
            'sequence': self.getAsList()
        })


class Parser(object):
    '''
    A wrapper around a callable of type
    `[t] -> s -> ME e ([t], s, a)`, to create a `Parser e s (m t) a`.
    Run the parser using the `parse` method.
    '''
    
    def __init__(self, parse):
        self.parse = parse


def checkFunction(fName, actual):
    if not hasattr(actual, '__call__'):
        obj = {
            'message' : 'type error',
            'function': fName,
            'expected': 'function',
            'actual'  : actual
        }
        raise TypeError(obj)
    # else: nothing to do

def checkParser(fName, actual):
    if not isinstance(actual, Parser):
        obj = {
            'message' : 'type error',
            'function': fName,
            'expected': 'Parser',
            'actual'  : actual
        }
        raise TypeError(obj)
    # else: nothing to do


def result(value, rest, state):
    return {'result': value, 'rest': rest, 'state': state}

def good(value, rest, state):
    return M.pure(result(value, rest, state))


def pure(x):
    '''
    a -> Parser e s (m t) a
    '''
    def f(xs, s):
        return good(x, xs, s)
    return Parser(f)

# Parser e s (m t) a
zero = Parser(functions.const_f(M.zero))

def error(e):
    '''
    e -> Parser e s (m t) a
    '''
    return Parser(functions.const_f(M.error(e)))

def fmap(g, parser):
    '''
    (a -> b) -> Parser e s (m t) a -> Parser e s (m t) b
    '''
    checkParser('fmap', parser)
    checkFunction('fmap', g)
    def h(r):
        return result(g(r['result']), r['rest'], r['state'])
    def f(xs, s):
        return parser.parse(xs, s).fmap(h)
    return Parser(f)

def bind(parser, g):
    '''
    Parser e s (m t) a -> (a -> Parser e s (m t) b) -> Parser e s (m t) b
    '''
    checkParser('bind', parser)
    checkFunction('bind', g)
    def f(xs, s):
        r = parser.parse(xs, s)
        val = r.value
        if r.status == 'success':
            return g(val['result']).parse(val['rest'], val['state'])
        else:
            return r
    return Parser(f)

def check(predicate, parser):
    '''
    (a -> Bool) -> Parser e s (m t) a -> Parser e s (m t) a
    '''
    checkFunction('check', predicate)
    checkParser('check', parser)
    return bind(parser, lambda value: pure(value) if predicate(value) else zero)

def update(f):
    '''
    (m t -> m t) -> Parser e s (m t) (m t)
    '''
    checkFunction('update', f)
    def g(xs, s):
        ys = f(xs)
        return good(ys, ys, s)
    return Parser(g)

# Parser e s (m t) (m t)
get = update(functions.id_f)

# m t -> Parser e s (m t) a
put = functions.compose(update, functions.const_f)

def updateState(g):
    '''
    (s -> s) -> Parser e s (m t) a
    '''
    checkFunction('updateState', g)
    def f(xs, s):
        new_state = g(s)
        return good(new_state, xs, new_state)
    return Parser(f)

# Parser e s (m t) s
getState = updateState(functions.id_f)

# s -> Parser e s (m t) a
putState = functions.compose(updateState, functions.const_f)

def many0(parser):
    '''
    Parser e s (m t) a -> Parser e s (m t) [a]
    '''
    checkParser('many0', parser)
    def f(xs, s):
        vals = []
        tokens = xs
        state = s
        while True:
            r = parser.parse(tokens, state)
            if r.status == 'success':
                vals.append(r.value['result'])
                state = r.value['state']
                tokens = r.value['rest']
            elif r.status == 'failure':
                return good(vals, tokens, state)
            else:  # must respect errors
                return r
    return Parser(f)

def many1(parser):
    '''
    Parser e s (m t) a -> Parser e s (m t) [a]
    '''
    checkParser('many1', parser)
    return check(lambda x: len(x) > 0, many0(parser))

def seq(parsers):
    '''
    [Parser e s (m t) a] -> Parser e s (m t) [a]
    '''
    for (ix, p) in enumerate(parsers):
        checkParser('seq-{}'.format(ix), p)
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

def appP(p, *parsers):
    '''
    Parser e s (m t) (a -> ... -> z) -> Parser e s (m t) a -> ... -> Parser e s (m t) z
    '''
    checkParser('appP', p)
    for (ix, parser) in enumerate(parsers):
        checkParser('appP-{}'.format(ix), parser)
    def g(f):
        return fmap(lambda args: f(*args), seq(parsers))
    return bind(p, g)

def app(f, *args):
    '''
    (a -> ... -> z) -> Parser e s (m t) a -> ... -> Parser e s (m t) z
    '''
    checkFunction('app', f)
    return appP(pure(f), *args)

def seq2L(p1, p2):
    '''
    Parser e s (m t) a -> Parser e s (m t) b -> Parser e s (m t) a
    '''
    checkParser('seq2L', p1)
    checkParser('seq2L', p2)
    return app(functions.first, p1, p2)

def seq2R(p1, p2):
    '''
    Parser e s (m t) a -> Parser e s (m t) b -> Parser e s (m t) b
    '''
    checkParser('seq2R', p1)
    checkParser('seq2R', p2)
    return app(functions.second, p1, p2)

def repeat(count, parser):
    '''
    Int -> Parser e s (m t) a -> Parser e s (m t) [a]
    '''
    checkParser('repeat', parser)
    return seq(functions.replicate(count, parser))

def lookahead(parser):
    '''
    Parser e s (m t) a -> Parser e s (m t) a
    '''
    checkParser('lookahead', parser)
    def g(xs):
        def h(s):
            return app(lambda a, _1, _2: a, parser, put(xs), putState(s))
        return bind(getState, h)
    return bind(get, g)

def not0(parser):
    '''
    Parser e s (m t) a -> Parser e s (m t) None
    '''
    checkParser('not0', parser)
    def f(xs, s):
        r = parser.parse(xs, s)
        if r.status == 'error':
            return r
        elif r.status == 'success':
            return M.zero
        else:
            return good(None, xs, s)
    return Parser(f)

def alt(parsers):
    '''
    [Parser e s (m t) a] -> Parser e s (m t) a
    '''
    for (ix, p) in enumerate(parsers):
        checkParser('alt-{}'.format(ix), p)
    def f(xs, s):
        r = M.zero
        for p in parsers:
            r = p.parse(xs, s)
            if r.status in ['success', 'error']:
                return r
        return r
    return Parser(f)

def optional(parser, default=None):
    '''
    Parser e s (m t) a -> a -> Parser e s (m t) a
    '''
    checkParser('optional', parser)
    return alt([parser, pure(default)])

def catchError(parser, f):
    '''
    Parser e s (m t) a -> (e -> Parser e s (m t) a) -> Parser e s (m t) a
    '''
    checkFunction('catchError', f)
    checkParser('catchError', parser)
    def g(xs, s):
        v = parser.parse(xs, s)
        if v.status == 'error':
            return f(v.value).parse(xs, s)
        return v
    return Parser(g)

def mapError(f, parser):
    '''
    (e -> e) -> Parser e s (m t) a -> Parser e s (m t) a
    '''
    checkFunction('mapError', f)
    checkParser('mapError', parser)
    return catchError(parser, functions.compose(error, f))

def commit(e, parser):
    '''
    e -> Parser e s (m t) a -> Parser e s (m t) a
    '''
    checkParser('commit', parser)
    return alt([parser, error(e)])

def addError(e, parser):
    '''
    e -> Parser [e] s (m t) a -> Parser [e] s (m t) a
    assumes errors are lists
    '''
    checkParser('addError', parser)
    return mapError(lambda es: functions.cons(e, es), parser)

def sepBy1(parser, separator):
    '''
    Parser e s (m t) a -> Parser e s (m t) b -> Parser e s (m t) (a, [(b, a)])
    '''
    checkParser('sepBy1', parser)
    checkParser('sepBy1', separator)
    return app(functions.pair, parser, many0(app(functions.pair, separator, parser)))

def sepBy0(parser, separator):
    '''
    Parser e s (m t) a -> Parser e s (m t) b -> Parser e s (m t) (Maybe (a, [(b, a)]))
    '''
    checkParser('sepBy0', parser)
    checkParser('sepBy0', separator)
    return optional(sepBy1(parser, separator))


class Itemizer(object):
    
    def __init__(self, f):
        '''
        f :: t -> s -> s
        '''
        checkFunction('Itemizer', f)
        self.f = f
        self.item = self._item()

    def _item(self):
        '''
        Parser e s (m t) t
        '''
        def g(xs, s):
            if xs.isEmpty():
                return M.zero
            first, rest = xs.first(), xs.rest()
            return good(first, rest, self.f(first, s))
        return Parser(g)

    def satisfy(self, pred):
        '''
        (t -> Bool) -> Parser e s (m t) t
        '''
        checkFunction('satisfy', pred)
        return check(pred, self.item)
    
    def literal(self, x):
        '''
        Eq t => t -> Parser e s (m t) t
        '''
        return self.satisfy(lambda y: x == y)

    def not1(self, parser):
        '''
        Parser e s (m t) a -> Parser e s (m t) t
        '''
        checkParser('not1', parser)
        return seq2R(not0(parser), self.item)

    def string(self, elems):
        '''
        Eq t => [t] -> Parser e s (m t) [t] 
        '''
        matcher = seq(list(map(self.literal, elems)))
        return seq2R(matcher, pure(elems))
    
    def oneOf(self, elems):
        c_set = set(elems)
        return self.satisfy(lambda x: x in c_set)


# doesn't do anything to the state
basic    = Itemizer(functions.second)
# assumes the state is a 2-tuple of integers (line, column)
position = Itemizer(functions.updatePosition)
# assumes that state is an integer -- how many tokens have been consumed
count    = Itemizer(lambda _, s: s + 1)


def run(parser, input_string, state=(1,1)):
    '''
    Run a parser given the token input and state.
    '''
    return parser.parse(ConsList(input_string), state)
