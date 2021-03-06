"""A template class for remote repos"""
from os import path
from urllib.parse import urlparse

from pomu.package import Package
from pomu.util.remote import get_full_cpv, filelist_to_cpvs

class RemoteRepo():
    """A class responsible for remotes"""
    def __init__(self, url):
        raise NotImplementedError()

    @classmethod
    def from_url(cls, uri, type_=None):
        tp = RemoteRepo.type_for_name(type_)
        if not tp:
            from pomu.repo.remote.git import RemoteGitRepo
            # no custom schemes for hg, assume git for common ones
            #from pomu.repo.remote.hg import RemoteHgRepo
            from pomu.repo.remote.rsync import RemoteRsyncRepo
            from pomu.repo.remote.svn import RemoteSvnRepo
            try:
                scheme, *_ = urlparse(uri)
            except:
                tp = RemoteGitRepo
            if (scheme.startswith('http') or scheme.startswith('git') or
                    scheme.startswith('ssh')):
                tp = RemoteGitRepo
            elif scheme.startswith('svn'):
                tp = RemoteSvnRepo
            elif scheme.startswith('rsync'):
                tp = RemoteRsyncRepo
        return tp(uri)

    @classmethod
    def type_for_name(cls, type_):
        from pomu.repo.remote.git import RemoteGitRepo
        from pomu.repo.remote.hg import RemoteHgRepo
        from pomu.repo.remote.rsync import RemoteRsyncRepo
        from pomu.repo.remote.svn import RemoteSvnRepo
        res = {'git': RemoteGitRepo, 'mercurial': RemoteHgRepo,
                'rsync': RemoteRsyncRepo, 'svn': RemoteSvnRepo}
        return res.get(type_)

    def fetch_package(self, name, category=None, version=None):
        """Fetches a package, determined by the parametres"""
        cat, n, ver = get_full_cpv(self.list_cpvs(), name, category, version).unwrap()
        ebuild = '{}/{}/{}-{}.ebuild'.format(cat, n, n, ver)
        subdir = '/{}/{}'.format(cat, name)
        filemap = {}
        filemap[ebuild] = self.fetch_file(ebuild).unwrap()
        subtree = self.fetch_subtree('/{}/{}/'.format(cat, name)).unwrap()
        for fpath in subtree:
            if '/' in fpath:
                parent, _, child = fpath.rpartition('/')
                if parent != 'files': continue
            if not fpath or fpath.endswith('.ebuild') or fpath.endswith('/'): continue
            p = path.join(subdir, fpath)
            filemap[p] = self.fetch_file(p).unwrap()
        return Package(name, '/', None, category, version, filemap=filemap)

    def list_cpvs(self):
        """Gets a list of all ebuilds in the repo"""
        return filelist_to_cpvs(self.fetch_tree())

    def fetch_tree(self):
        """Returns repos hierarchy"""
        raise NotImplementedError()

    def fetch_subtree(self, key):
        """Lists a subtree"""
        raise NotImplementedError()

    def fetch_file(self, key):
        """Fetches a file from the repo"""
        raise NotImplementedError()

def normalize_key(key, trail=False):
    k = '/' + key.lstrip('/')
    if trail:
        k = k.rstrip('/') + '/'
    return k
