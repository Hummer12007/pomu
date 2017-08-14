"""A class for remote svn repos"""
from subprocess import run

from pomu.repo.remote import RemoteRepo, normalize_key
from pomu.util.result import Result

class RemoteSvnRepo(RemoteRepo):
    """A class responsible for svn remotes"""
    def __init__(self, url):
        self.uri = uri

    def __enter__(self):
        pass

    def __exit__(self, *_):
        pass

    def fetch_tree(self):
        """Returns repos hierarchy"""
        if hasattr(self, '_tree'):
            return self._tree
        p = run('svn', 'ls', '-R', self.uri)
        if p.returncode:
            return []
        self._tree = p.stdout.split('\n')
        return self._tree

    def fetch_subtree(self, key):
        """Lists a subtree"""
        k = normalize_key(key, True)
        self.fetch_tree()
        dic = dict(self._tree)
        if k not in dic:
            return Result.Err()
        l = len(key)
        return Result.Ok(
                [tpath[l:] for tpath in self.fetch_tree() if tpath.startswith(k)])

    def fetch_file(self, key):
        """Fetches a file from the repo"""
        k = normalize_key(key)
        self.fetch_tree()
        dic = dict(self._tree)
        if k not in dic:
            return Result.Err()
        p = run('svn', 'cat', k)
        if p.returncode:
            return Result.Err()
        return Result.Ok(p.stdout)
