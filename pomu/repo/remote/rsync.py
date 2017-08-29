"""A class for remote rsync repos"""
from os import mkdtemp, rmdir, mkfifo, unlink, path
from subprocess import run

from pomu.repo.remote.remote import RemoteRepo, normalize_key
from pomu.util.result import Result

class RemoteRsyncRepo(RemoteRepo):
    """A class responsible for rsync remotes"""
    def __init__(self, url):
        self.uri = url

    def __enter__(self):
        pass

    def __exit__(self, *_):
        pass

    def fetch_tree(self):
        """Returns repos hierarchy"""
        if hasattr(self, '_tree'):
            return self._tree
        d = mkdtemp()
        p = run('rsync', '-rn', '--out-format="%n"', self.uri, d)
        rmdir(d)
        if p.returncode:
            return Result.Err()
        self._tree = ['/' + x for x in p.stdout.split('\n')]
        return self._tree

    def fetch_subtree(self, key):
        """Lists a subtree"""
        k = normalize_key(key, True)
        self.fetch_tree()
        dic = dict(self._tree)
        if k not in dic:
            return []
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
        d = mkdtemp()
        fip = path.join(d, 'fifo')
        mkfifo(fip)
        p = run('rsync', self.uri.rstrip('/') + key, fip)
        fout = fip.read()
        unlink(fip)
        rmdir(d)
        if p.returncode:
            return Result.Err()
        return Result.Ok(fout)
