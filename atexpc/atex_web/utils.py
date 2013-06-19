from operator import itemgetter
from itertools import groupby
from itertools import izip, chain, repeat

def group_in(n, items):
    return [[item for i, item in group] for i, group
            in groupby(sorted((i % n, item) for i, item in enumerate(items)),
                       itemgetter(0))]

def grouper(n, iterable, padvalue=None):
    "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
    return izip(*[chain(iterable, repeat(padvalue, n-1))]*n)