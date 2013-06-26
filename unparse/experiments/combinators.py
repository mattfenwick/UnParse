
def parserFactory(Type):
    '''
    in: a class `m` which implements:
      - pure      ::  a -> m a
      - fmap      ::  m a -> (a -> b) -> m b
      - plus      ::  m a -> m a -> m a
      - error     ::  e -> m a
      - zero      ::  m a
      - mapError  ::  m a -> (e -> e) -> m a
    '''

    def result(value, rest, state):
        return {'result': value, 'rest': rest, 'state': state}

    def good(value, rest, state):
        return Type.pure(result(value, rest, state))

    class Parser(object):
        '''
        Parsers are parameterized by four types:
         - `e`:  error
         - `s`:  user state
         - `m`:  token sequence
         - `t`:  token
         - `a`:  result
        
        which is written:  `Parser e s (m t) a`
        
        the `m` type argument -- the sequence type that holds the tokens --
        must support these operations:
         - isEmpty :: m t -> Bool
         - first   :: m t -> t
         - rest    :: m t -> m t
        
        Parsers can be created by passing an appropriate function to the
        constructor, or also from existing parsers using instance 
        and static methods.  In addition, there are a few static fields --
        `Parser.item`, `Parser.zero`, `Parser.get`, and `Parser.getState`
        -- which are parsers implementing basic parsing operations.
        '''

        def __init__(self, parse):
            '''
            `parse`: a function of two arguments:
             1. the token sequence
             2. the user state
            '''
            self.parse = parse

        def fmap(self, g):
            '''
            Parser e s (m t) a -> (a -> b) -> Parser e s (m t) b
            '''
            def h(r):
                return result(g(r['result']), r['rest'], r['state'])
            def f(xs, s):
                return self.parse(xs, s).fmap(h)
            return Parser(f)

        @staticmethod
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
                return Type.error(e)
            return Parser(f)

        def mapError(self, g):
            '''
            Parser e s (m t) a -> (e -> e) -> Parser e s (m t) a
            '''
            def f(xs, s):
                return self.parse(xs, s).mapError(g)
            return Parser(f)

        @staticmethod
        def put(xs):
            '''
            m t -> Parser e s (m t) a
            '''
            def f(_xs_, s):
                return good(None, xs, s)
            return Parser(f)

        @staticmethod
        def putState(s):
            '''
            s -> Parser e s (m t) a
            '''
            def f(xs, _s_):
                return good(None, xs, s)
            return Parser(f)

        @staticmethod
        def updateState(g):
            '''
            (s -> s) -> Parser e s (m t) a
            '''
            def f(xs, s):
                return good(None, xs, g(s))
            return Parser(f)

        def check(self, p):
            '''
            Parser e s (m t) a -> (a -> Bool) -> Parser e s (m t) a
            '''
            def f(xs, s):
                r = self.parse(xs, s)
                if r.status != 'success':
                    return r
                elif p(r.value['result']):
                    return r
                return Type.zero
            return Parser(f)

        @staticmethod
        def literal(x):
            '''
            Eq t => t -> Parser e s (m t) t
            '''
            return Parser.item.check(lambda y: x == y)

        @staticmethod
        def satisfy(pred):
            '''
            (t -> Bool) -> Parser e s (m t) t
            '''
            return Parser.item.check(pred)

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
            return self.many0().check(lambda x: len(x) > 0)

        @staticmethod
        def all(parsers):
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

        @staticmethod
        def app(f, *parsers):
            '''
            (a -> ... y -> z) -> Parser e s (m t) a -> ... -> Parser e s (m t) y -> Parser e s (m t) z
            '''
            return Parser.all(parsers).fmap(lambda rs: f(*rs))

        def optional(self, x):
            '''
            Parser e s (m t) a -> a -> Parser e s (m t) a
            '''
            return self.plus(Parser.pure(x))

        def seq2L(self, other):
            '''
            Parser e s (m t) a -> Parser e s (m t) b -> Parser e s (m t) a
            '''
            def f(x):
                return x[0]
            return Parser.all([self, other]).fmap(f)

        def seq2R(self, other):
            '''
            Parser e s (m t) a -> Parser e s (m t) b -> Parser e s (m t) b
            '''
            def g(x):
                return x[1]
            return Parser.all([self, other]).fmap(g)

        def not0(self):
            '''
            Parser e s (m t) a -> Parser e s (m t) None
            '''
            def f(xs, s):
                r = self.parse(xs, s)
                if r.status == 'error':
                    return r
                elif r.status == 'success':
                    return Type.zero
                else:
                    return good(None, xs, s)
            return Parser(f)

        def not1(self):
            '''
            Parser e s (m t) a -> Parser e s (m t) t
            '''
            return self.not0().seq2R(Parser.item)

        def commit(self, e):
            '''
            Parser e s (m t) a -> e -> Parser e s (m t) a
            '''
            return self.plus(Parser.error(e))

        @staticmethod
        def string(elems):
            '''
            Eq t => [t] -> Parser e s (m t) [t] 
            '''
            matcher = Parser.all(map(Parser.literal, elems))
            return matcher.seq2R(Parser.pure(elems))

        @staticmethod
        def any(parsers):
            '''
            [Parser e s (m t) a] -> Parser e s (m t) a
            '''
            def f(xs, s):
                r = Type.zero
                for p in parsers:
                    r = p.parse(xs, s)
                    if r.status in ['success', 'error']:
                        return r
                return r
            return Parser(f)


    # defined outside the class b/c they're constants

    # Parser e s (m t) a
    Parser.zero = Parser(lambda xs, s: Type.zero)

    def f_item(xs, s):
        if xs.isEmpty():
            return Type.zero
        first, rest = xs.first(), xs.rest()
        return good(first, rest, s)

    # Parser e s (m t) t
    Parser.item = Parser(f_item)

    def f_get(xs, s):
        return good(xs, xs, s)

    # Parser e s (m t) (m t)
    Parser.get = Parser(f_get)

    def f_getState(xs, s):
        return good(s, xs, s)

    # Parser e s (m t) s
    Parser.getState = Parser(f_getState)


    return Parser
