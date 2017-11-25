"""A class for remote git repos"""
from os import chdir, path
from shutil import rmtree
from subprocess import call
from tempfile import mkdtemp

from git import Repo

from pomu.repo.remote.remote import RemoteRepo, normalize_key
from pomu.util.git import parse_object
from pomu.util.result import Result

class RemoteGitRepo(RemoteRepo):
    """A class responsible for git remotes"""
    def __init__(self, url):
        self.uri = url
        self.dir = mkdtemp()
        if call(['git', 'clone', '--depth=1', '--bare', url, self.dir]) > 0: # we've a problem
            raise RuntimeError()
        self.repo = Repo(self.dir)

    def __enter__(self):
        pass

    def __exit__(self, *_):
        self.cleanup()

    def get_object(self, oid):
        head, tail = oid[0:2], oid[2:]
        opath = path.join(self.dir, 'objects', head, tail)
        return open(opath, 'rb').read()

    def _fetch_tree(self, obj, tpath):
        res = []
        ents = parse_object(self.get_object(obj), tpath).unwrap()
        for is_dir, sha, opath in ents:
            res.append((opath.decode('utf-8') + ('/' if is_dir else ''), sha))
            if is_dir:
                res.extend(self._fetch_tree(sha, opath))
        return res

    def fetch_tree(self):
        """Returns repos hierarchy"""
        if hasattr(self, '_tree'):
            return [x for x, y in self._tree]
        tid = self.repo.tree().hexsha
        res = self._fetch_tree(tid, b'')
        self._tree = res
        return [x for x, y in res]

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
        return parse_object(self.get_object(dic[k]))

    def cleanup(self):
        rmtree(self.dir)
