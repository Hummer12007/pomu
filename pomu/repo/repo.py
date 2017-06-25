"""Subroutines with repositories"""
from os import path, makedirs, rmdir
from shutil import copy2

from git import Repo
import portage

from pomu.util.cache import cached
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
        return Repo(self.root)

    @property
    def pomu_dir(self):
        return path.join(self.root, 'metadata/pomu')

    def merge(self, package):
        """Merge a package into the repository"""
        r = self.repo
        pkgdir = path.join(self.pomu_dir, package.category, package.name)
        if slot != 0:
            pkgdir = path.join(pkgdir, slot)
        package.merge_into(self.root).expect('Failed to merge package')
        for wd, f in package.files:
            r.index.add(path.join(dst, f))
        manifests = package.gen_manifests(self.root).expect()
        for m in manifests:
            r.index.add(m)
        self.write_meta(pkgdir, package, manifests)
        with open(path.join(self.pomu_dir, 'world'), 'a+') as f:
            f.write(package.category, '/', package.name)
            f.write('\n' if package.slot == '0' else ':{}\n'.format(package.slot))
        r.index.add(path.join(self.pomu_dir, package.name))
        r.index.add(self.pomu_dir)
        r.index.commit('Merged package ' + package.name)
        return Result.Ok('Merged package ' + package.name + ' successfully')

    def write_meta(self, pkgdir, package, manifests):
        with open(path.join(pkgdir, 'FILES'), 'w') as f:
            for w, f in package.files:
                f.write('{}/{}\n'.format(w, f))
            for m in manifests:
                f.write('{}\n'.format(strip_prefix(m, self.root)))
        if package.backend:
            with open(path.join(pkgdir, 'BACKEND'), 'w') as f:
                f.write('{}\n'.format(package.backend.__name__))
            package.backend.write_meta(pkgdir)
        with open(path.join(pkgdir, 'VERSION')) as f:
            f.write(package.version)

    def unmerge(self, package):
        """Remove a package (by contents) from the repository"""
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
        """Remove a package (by name) from the repository"""
        r = self.repo
        pf = path.join(self.pomu_dir, name, 'FILES')
        if not path.isfile(pf):
            return Result.Err('Package not found')
        with open(pf, 'w') as f:
            for insf in f:
                remove_file(path.join(self.root, insf))
        remove_file(path.join(self.pomu_dir, name))
        r.commit('Removed package ' + name + ' successfully')
        return Result.Ok('Removed package ' + name + ' successfully')

    def get_package(self, category, name, slot='0'):
        """Get a package by name"""
        with open(path.join(self.pomu_dir, 'world'), 'r') as f:
            lines = [x.strip() for x in f]
            if slot == '0':
                spec = '{}/{}'.format(category, name)
            else:
                spec = '{}/{}:{}'.format(category, name, slot)
            if not lines.has(spec):
                return Result.Err('Package not found')
        if slot == '0':
            pkgdir = path.join(self.pomu_dir, category, name)
        else:
            pkgdir = path.join(self.pomu_dir, category, name, slot)
        with open(path.join(pkgdir, 'BACKEND'), 'r') as f:
            bname = f.readline().strip()
        backend = dispatcher.backends[bname].from_meta_dir(pkgdir)
        with open(path.join(pkgdir, 'VERSION'), 'r') as f:
            version = f.readline().strip()
        with open(path.join(pkgdir, 'FILES'), 'r') as f:
            files = [x.strip() for x in f]
        return Package(backend, name, self.root, category=category, version=version, slot=slot, files=files)


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

def pomu_active_portage_repo():
    """Returns a portage repo, for which pomu is enabled"""
    for repo in portage_repos():
        if pomu_status(portage_repo_path(repo)):
            return repo
    return None

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
