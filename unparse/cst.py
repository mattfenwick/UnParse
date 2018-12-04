'''
@author: matt
'''
from .combinators import (checkParser, bind, getState, commit, addError, seq, fmap, app)


def _forbid_duplicates(arr):
    keys = set()
    for a in arr:
        if a in keys:
            raise Exception("duplicate name -- {}".format(a))
        keys.add(a)

def _forbid_keys(forbidden, keys):
    key_set = set(keys)
    for key in forbidden:
        if key in key_set:
            raise Exception('cst node: forbidden key: {}'.format(key))

def cut(message, parser):
    '''
    e -> Parser [(e, s)] s (m t) a -> Parser [(e, s)] s (m t) a
    '''
    checkParser('cut', parser)
    def f(state):
        return commit([(message, state)], parser)
    return bind(getState, f)

def addErrorState(e, parser):
    '''
     e -> Parser [(e, s)] s (m t) a -> Parser [(e, s)] s (m t) a
    '''
    checkParser('addErrorState', parser)
    def g(state):
        return addError((e, state), parser)
    return bind(getState, g)

# wish I could put `pairs` in a kwargs dictionary, but then the order would be lost
def node(name, *pairs):
    """
    1. runs parsers in sequence
    2. collects results into a dictionary
    3. grabs state at which parsers started
    4. adds an error frame
    """
    names = [x for (x, _) in pairs]
    _forbid_duplicates(names)
    _forbid_keys(['_name', '_start', '_end'], names)
    def action(start, results, end):
        out = dict(results)
        out['_start'] = start
        out['_name'] = name
        out['_end'] = end
        return out
    def closure_workaround(a):
        '''captures value of a'''
        return lambda b: (a, b)
    child_parsers = seq([fmap(closure_workaround(parser_name), parser) for (parser_name, parser) in pairs])
    return addErrorState(name, app(action, getState, child_parsers, getState))
