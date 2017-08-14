"""Miscellaneous utility functions for git structures"""

from base64 import b16encode
import zlib

from pomu.util.result import Result

def parse_tree(blob, path=''):
    """Parses a git tree"""
    res = []
    leng, _, tree = blob.partition(b'\0')
    if not tree:
        return Result.Err('Invalid tree')
    while len(tree) > 0:
        mode, _, tree = tree.partition(b' ')
        name, _, tree = tree.partition(b'\0')
        sha = b16encode(tree[0:20]).decode('utf-8').lower()
        tree = tree[20:]
        if not name or not sha:
            return Result.Err()
        is_dir = mode[0:1] != b'1'
        res.append((is_dir, sha, path.encode('utf-8') + b'/' + name))
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
    if data[0:5] == b'blob ':
        return parse_blob(data[5:])
    elif data[0:5] == b'tree ':
        return parse_tree(data[5:])
    return Result.Err('Unsupported object type')
