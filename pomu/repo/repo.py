"""Subroutines with repositories"""
from os import path, mkdirs, remove, rmdir
from shutil import copy2

from git import Repo
import portage

class Repository():
    def __init__(self, path):
        if not pomu_status(path):
            raise ValueError('This path is not a valid pomu repository')
        self.root = root

    repo = property()
    @repo.getter
    def repo(self):
        return Repo(repo_path)

    def merge(self, package):
        r = self.repo
        for wd, f in package.files:
            dst = path.join(self.root, wd)
            os.makedirs(dst)
            copy2(path.join(package.root, wd, f), dst)
            r.index.add(path.join(dst, f))
        r.index.commit('Merged package ' + package.name)
        return Result.Ok('Merged package ' + package.name ' successfully')

    def unmerge(self, package):
        r = self.repo
        for wd, f in package.files:
            dst = path.join(self.root, wd)
            r.index.remove(path.join(package.root, wd, f)
            try:
                rmdir(dst)
            except OSError: pass
        self.repo.commit('Removed package ' + package.name + ' successfully')


def portage_repos():
    """Yield the repositories configured for portage"""
    rsets = portage.db[portage.root]['vartree'].settings.repositories

    for repo in rsets.prepos_order:
        yield repo

def portage_repo_path(repo):
    """Get the path of a given portage repository"""
    rsets = portage.db[portage.root]['vartree'].settings.repositories

    if repo in rsets.prepos:
        return rsets.prepos[repo].location
    return None

def pomu_status(repo_path):
    """Check if pomu is enabled for a repository at a given path"""
    return path.isdir(path.join(repo_path, 'metadata', 'pomu'))

def pomu_active_repo():
    """Returns a portage repo, for which pomu is enabled"""
    for repo in portage_repos():
        if pomu_status(portage_repo_path(repo)):
            return repo
    return None
