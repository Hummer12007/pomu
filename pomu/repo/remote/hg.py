"""A class for remote hg repos"""
from os import chdir, mkdtemp
from shutil import rmtree
from subprocess import call, run

from pomu.repo.remote.remote import RemoteRepo, normalize_key
from pomu.util.result import Result

class RemoteHgRepo(RemoteRepo):
    """A class responsible for hg remotes"""
    def __init__(self, url):
        self.uri = url
        self.dir = mkdtemp()
        chdir(self.dir)
        if call('hg', 'clone', '-U', url, '.') > 0: # we've a problem
            raise RuntimeError()

    def __enter__(self):
        pass

    def __exit__(self, *_):
        self.cleanup()

    def fetch_tree(self):
        """Returns repos hierarchy"""
        if hasattr(self, '_tree'):
            return self._tree
        p = run('hg', 'files', '-rdefault')
        if p.returncode:
            return []
        self._tree = ['/' + x for x in p.stdout.split('\n')]
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
        p = run('hg', 'cat', '-rdefault', k)
        if p.returncode:
            return Result.Err()
        return Result.Ok(p.stdout)

    def cleanup(self):
        rmtree(self.dir)
