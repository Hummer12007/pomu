"""Subroutines with repositories"""
from os import path, makedirs, remove, rmdir
from shutil import copy2

from git import Repo
import portage

from pomu.util.fs import remove_file
from pomu.util.result import Result

class Repository():
    def __init__(self, root, name=None):
        if not pomu_status(root):
            raise ValueError('This path is not a valid pomu repository')
        self.root = root
        self.name = name

    @property
    def repo(self):
        return Repo(repo_path)

    @property
    def pomu_dir(self):
        return path.join(self.root, 'metadata/pomu')

    def merge(self, package):
        r = self.repo
        for wd, f in package.files:
            dst = path.join(self.root, wd)
            os.makedirs(dst)
            copy2(path.join(package.root, wd, f), dst)
            r.index.add(path.join(dst, f))
        with open(path.join(self.pomu_dir, package.name), 'w') as f:
            f.write('{}/{}'.format(wd, f))
        r.index.add(path.join(self.pomu_dir, package.name))
        r.index.commit('Merged package ' + package.name)
        return Result.Ok('Merged package ' + package.name + ' successfully')

    def unmerge(self, package):
        r = self.repo
        for wd, f in package.files:
            dst = path.join(self.root, wd)
            remove_file(path.join(dst, f))
            try:
                rmdir(dst)
            except OSError: pass
        pf = path.join(self.pomu_dir, package.name)
        if path.isfile(pf):
            remove_file(pf)
        r.commit('Removed package ' + package.name + ' successfully')
        return Result.Ok('Removed package ' + package.name + ' successfully')

    def remove_package(self, name):
        pf = path.join(self.pomu_dir, package.name)
        if not path.isfile(pf):
            return Result.Err('Package not found')
        with open(pf, 'w') as f:
            for insf in f:
                remove_file(path.join(self.root, insf))
        remove_file(pf)
        r.commit('Removed package ' + package.name + ' successfully')
        return Result.Ok('Removed package ' + package.name + ' successfully')



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

@cached
def pomu_active_repo(no_portage=None, repo_path=None):
    """Returns a repo for which pomu is enabled"""
    if no_portage:
        if not repo_path:
            return Result.Err('repo-path required')
        if pomu_status('repo_path'):
            return Result.Ok(Repository(repo_path))
        return Result.Err('pomu is not initialized')
    else:
        repo = pomu_active_portage_repo()
        if repo:
            return Result.Ok(portage_repo_path(repo), repo)
        return Result.Err('pomu is not initialized')
