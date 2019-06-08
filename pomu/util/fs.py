"""
Filesystem utils
"""
import os

def strip_prefix(string, prefix):
    """Returns a string, stripped from its prefix"""
    if not prefix.endswith('/'):
        aprefix = prefix + '/'
        if string.startswith(aprefix):
            return string[len(aprefix):]
    if string.startswith(prefix):
        return string[len(prefix):]
    else:
        return string

def remove_file(repo, dst):
    """
    Removes a file from a repository (adding changes to the index)
    Parameters:
        repo - the repo
        dst - the file
    """
    repo.index.remove(dst)
    os.remove(dst)
