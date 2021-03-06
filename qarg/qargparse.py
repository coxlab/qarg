#!/usr/bin/env python
"""
    syntax:
        comma seperated list of args

        args:
            <sname>(<lname>{<dest>[<type>=<default>@<action>#<nargs>$<const>

        all but sname are optional
        if lname is missing, sname will be used
        if lname is missing, and sname has len > 1
            long name will be sname and sname will be the
            first character of sname

    examples:
        f(foo)[int]=10
        f[int]=10

    add_argument options
        name or flags (short name & long name)
        action = '@'
        nargs = '#'
        const = '$'
        default = '='
        type = '['
        choices =
        required = '!'
        help =
        metavar =
        dest = '{'
"""


import argparse


type_lookup = {
    'int': int, 'str': str, 'bool': bool, 'float': float,
    'long': long, 'complex': complex, 'unicode': unicode,
    'list': list, 'tuple': tuple, 'bytearray': bytearray,
    'buffer': buffer, 'set': set, 'frozenset': frozenset,
    'dict': dict, 'memoryview': memoryview}

cmap = {
    '$': 'const',
    '#': 'nargs',
    '@': 'action',
    '=': 'default',
    '{': 'dest',
    '[': 'type',
    '(': 'lname',
}

endcs = ''.join(cmap.keys())


def lookup_type(typestring):
    if typestring in type_lookup:
        return type_lookup[typestring]
    raise TypeError("Unknown type string: %s" % typestring)


def extract(token, key):
    if key not in token:
        return token, False, None
    si = token.index(key)
    ei = None
    for ei in xrange(si + 1, len(token)):
        if token[ei] in endcs:
            break
        ei += 1  # allows ei to equal the end of the token
    if ei is None:
        raise ValueError('Failed to extract %s from %s' % (key, token))
    return token[:si] + token[ei:], True, token[si + 1:ei]


def parse_token(token):
    """
    Return args and kwargs for ArgumentParser.add_argument
    """
    kwargs = {}

    if '!' in token:
        token = token.replace('!', '')
        kwargs['required'] = True

    for (c, key) in cmap.iteritems():
        token, r, value = extract(token, c)
        if r:
            kwargs[key] = value

    # correct nargs
    if 'nargs' in kwargs:
        if kwargs['nargs'] not in ('?*+R'):
            kwargs['nargs'] = int(kwargs['nargs'])
        elif kwargs['nargs'] == 'R':
            kwargs['nargs'] = argparse.REMAINDER

    # lookup type
    if 'type' in kwargs:
        kwargs['type'] = lookup_type(kwargs['type'])
        if 'default' in kwargs:
            kwargs['default'] = kwargs['type'](kwargs['default'])
        if 'const' in kwargs:
            kwargs['const'] = kwargs['type'](kwargs['const'])
            if not (('nargs' in kwargs) and (kwargs['nargs'] == '?')):
                # remove type as it conflicts with const
                # if nargs != '?'
                del kwargs['type']

    lname = kwargs.pop('lname', token)
    sname = token[0]

    args = ('-%s' % sname, '--%s' % lname)
    return args, kwargs


def parse(arg_string, description=None):
    """
    make an argparser from arg_string

    syntax:
        comma seperated list of args

        args:
            <sname>(<lname>{<dest>[<type>=<default>@<action>#<nargs>$<const>

        all but sname are optional
        if lname is missing, sname will be used
        if lname is missing, and sname has len > 1
            long name will be sname and sname will be the
            first character of sname

    examples:
        f(foo[int=10
        f[int=10

    add_argument options
        name or flags (short name & long name)
        action = '@'
        nargs = '#'
        const = '$'
        default = '='
        type = '['
        choices =
        required = '!'
        help =
        metavar =
        dest = '{'
    """
    if description is None:
        description = "Autogenerated parser from string: %s" % arg_string
    parser = argparse.ArgumentParser(description=description)
    for t in arg_string.split(','):
        args, kwargs = parse_token(t)
        parser.add_argument(*args, **kwargs)
    return parser


def get(arg_string, args=None, namespace=None,
        partial=False, return_leftover=False):
    p = parse(arg_string)
    if partial:
        ns, leftover = p.parse_known_args(args, namespace)
        if return_leftover:
            return ns, leftover
        return ns
    return p.parse_args(args, namespace)


def test():
    ns = get('f', args=['-f', 'foo'])
    assert hasattr(ns, 'f')
    assert type(ns.f) == str
    assert ns.f == 'foo'

    ns = get('f,b', args=['-f', 'foo', '-b', 'bar'])
    assert hasattr(ns, 'f')
    assert hasattr(ns, 'b')
    assert ns.f == 'foo'
    assert ns.b == 'bar'

    ns = get('f(foo', args=['-f', 'foo'])
    assert hasattr(ns, 'foo')
    assert type(ns.foo) == str
    assert ns.foo == 'foo'

    ns = get('f(foo[int', args=['-f', '1'])
    assert type(ns.foo) == int
    assert ns.foo == 1

    ns = get('f(foo[int=1', args=['-f', '2'])
    assert ns.foo == 2

    ns = get('f(foo[int=1', args=[])
    assert ns.foo == 1

    ns = get('f(foo@store_true,b(bar@store_false',
             args=[])
    assert ns.foo is False
    assert ns.bar is True

    ns = get('f(foo@store_true,b(bar@store_false',
             args=['-f', '-b'])
    assert ns.foo is True
    assert ns.bar is False

    # TODO add more tests
