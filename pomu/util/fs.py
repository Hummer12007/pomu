"""
Filesystem utils
"""
import os

def strip_prefix(string, prefix):
    """Returns a string, stripped from its prefix"""
    if string.startswith(prefix):
        return string[len(prefix):]
    else:
        return string

def remove_file(repo, dst):
    repo.index.remove(dst)
    os.remove(dst)
