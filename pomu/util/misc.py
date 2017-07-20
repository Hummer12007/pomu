"""Miscellaneous utility functions"""
import re

def list_add(dst, src):
    """
    Extends the target list with a scalar, or contents of the given list
    """
    if isinstance(src, list):
        dst.extend(src)
    else:
        dst.append(src)


def pivot(string, idx, keep_pivot=False):
    """
    A function to split a string in two, pivoting at string[idx].
    If keep_pivot is set, the pivot character is included in the second string.
    Alternatively, it is omitted.
    """
    if keep_pivot:
        return (string[:idx], string[idx:])
    else:
        return (string[:idx], string[idx+1:])

def extract_urls(text):
    """Extracts URLs from arbitrary text"""
    schemas = ['http://', 'https://', 'ftp://', 'ftps://']
    words = list(filter(lambda x: any(y in x for y in schemas), text.split()))
    maxshift = lambda x: max(x.find(y) for y in schemas)
    links = [x[maxshift(x):].rstrip('\'")>.,') for x in words]
    return links

def parse_range(text, max_num=None):
    """Parses a numeric range (e.g. 1-2,5-16)"""
    text = re.sub('\s*-\s*', '-', text)
    subranges = [x.strip() for x in text.split(',')]
    subs = []
    maxint = -1
    for sub in subranges:
        l, _, r = sub.partition('-')
        if not l and not _:
            continue
        if (l and not l.isdigit()) or (r and not r.isdigit()):
            return Result.Err('Invalid subrange: {}'.format(sub))
        if l:
            l = int(l)
            maxint = max(l, maxint)
        if r:
            r = int(r)
            maxint = max(r, maxint)
        if _:
            subs.append((l if l else 1, r if r else -1))
        else:
            subs.append((l, None))
    if max_num:
        maxint = max_num
    res = set()
    add = lambda x: res.add(x) if x <= maxint else None
    for l, r in subs:
        if not r:
            add(l)
            continue
        if r == -1:
            r = maxint
        for x in range(l, r + 1):
            add(x)
    return Result.Ok(res)

