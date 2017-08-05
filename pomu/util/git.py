"""Miscellaneous utility functions for git structures"""

from base64 import b16encode

from pomu.util.result import Result

def parse_tree(blob):
    """Parses a git tree"""
    res = []
    leng, _, tree = blob.partition('\0')
    if not tree:
        return Result.Err('Invalid tree')
    while len(data) > 0:
        data = data[7:] # strip access code
        name, _, data = data.partition('\0')
        sha = b16encode(data[0:20]).decode('utf-8')
        data = data[20:]
        if not name or not sha:
            return Result.Err()
        res.append((sha, name))
    return Result.Ok(res)

def parse_blob(blob):
    """Parses a git blob"""
    data = zlib.decompress(blob)
    leng, _, data = data.partition('\0')
    if not leng or not data:
        return Result.Err()

def commit_head(blob):
    if not blob[7:] == 'commit ':
        return Result.Err()
    l = blob.split('\n')[0]
    cid, _, tid = l.partition('\0')
    if not tid[0:5] == 'tree ':
        return Result.Err()
    return tid[5:]

def parse_object(obj):
    """Parses a git object"""
    data = zlib.decompress(obj)
    if data[0:5] == 'blob ':
        return parse_blob(data[5:])
    elif data[0:5] == 'tree ':
        return parse_tree(data[5:])
    return Result.Err('Unsupported object type')
