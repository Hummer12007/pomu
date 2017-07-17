"""Subroutines with repositories"""
123
from os import path, rmdir, makedirs
from shutil import copy2

from git import Repo
from patch import PatchSet
import portage

from pomu.package import Package
from pomu.util.cache import cached
from pomu.util.fs import remove_file, strip_prefix
from pomu.util.result import Result

class Repository():
    def __init__(self, root, name=None):
        """
        Parameters:
            root - root of the repository
            name - name of the repository
        """
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
        """Merge a package (a pomu.package.Package package) into the repository"""
        r = self.repo
        pkgdir = path.join(self.pomu_dir, package.category, package.name)
        if package.slot != '0':
            pkgdir = path.join(pkgdir, package.slot)
        package.merge_into(self.root).expect('Failed to merge package')
        for wd, f in package.files:
            r.index.add([path.join(wd, f)])
        manifests = package.gen_manifests(self.root).expect()
        for m in manifests:
            r.index.add([m])
        self.write_meta(pkgdir, package, manifests)
        with open(path.join(self.pomu_dir, 'world'), 'a+') as f:
            f.write('{}/{}'.format(package.category, package.name))
            f.write('\n' if package.slot == '0' else ':{}\n'.format(package.slot))
        r.index.add([path.join(self.pomu_dir, package.category, package.name)])
        r.index.add([path.join(self.pomu_dir, 'world')])
        r.index.commit('Merged package ' + package.name)
        return Result.Ok('Merged package ' + package.name + ' successfully')

    def write_meta(self, pkgdir, package, manifests):
        """
        Write metadata for a Package object
        Parameters:
            pkgdir - destination directory
            package - the package object
            manifests - list of generated manifest files
        """
        makedirs(pkgdir, exist_ok=True)
        with open(path.join(pkgdir, 'FILES'), 'w+') as f:
            for wd, fil in package.files:
                f.write('{}/{}\n'.format(wd, fil))
            for m in manifests:
                f.write('{}\n'.format(strip_prefix(m, self.root)))
        if package.patches:
            patch_dir = path.join(pkgdir, 'patches')
            makedirs(patch_dir, exist_ok=True)
            with open(path.join(pkgdir, 'PATCH_ORDER'), 'w') as f:
                for patch in package.patches:
                    copy2(patch, patch_dir)
                    f.write(path.basename(patch) + '\n')
        if package.backend:
            with open(path.join(pkgdir, 'BACKEND'), 'w+') as f:
                f.write('{}\n'.format(package.backend.__name__))
            package.backend.write_meta(pkgdir)
        with open(path.join(pkgdir, 'VERSION'), 'w+') as f:
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
        pkg = self.get_package(name).expect()
        return self.unmerge(pkg)

    def _get_package(self, category, name, slot='0'):
        """Get an existing package (by category, name and slot), reading the manifest"""
        from pomu.source import dispatcher
        if slot == '0':
            pkgdir = path.join(self.pomu_dir, category, name)
        else:
            pkgdir = path.join(self.pomu_dir, category, name, slot)
        backend = None
        if path.exists(path.join(pkgdir, 'BACKEND')):
            with open(path.join(pkgdir, 'BACKEND'), 'r') as f:
                bname = f.readline().strip()
            backend = dispatcher.backends[bname].from_meta_dir(pkgdir)
        with open(path.join(pkgdir, 'VERSION'), 'r') as f:
            version = f.readline().strip()
        with open(path.join(pkgdir, 'FILES'), 'r') as f:
            files = [x.strip() for x in f]
        patches=[]
        if path.isfile(path.join(pkgdir, 'PATCH_ORDER')):
            with open(path.join(pkgdir, 'PATCH_ORDER'), 'r') as f:
                patches = [x.strip() for x in f]
        pkg = Package(name, self.root, backend, category=category, version=version, slot=slot, files=files, patches=[path.join(pkgdir, 'patches', x) for x in patches])
        pkg.__class__ = MergedPackage
        return pkg

    def get_package(self, name, category=None, slot=None):
        """Get a package by name, category and slot"""
        with open(path.join(self.pomu_dir, 'world'), 'r') as f:
            for spec in f:
                cat, _, nam = spec.partition('/')
                nam, _, slo = nam.partition(':')
                if (not category or category == cat) and nam == name:
                    if not slot or (slot == '0' and not slo) or slot == slo:
                        return self._get_package(category, name, slot)
        return Result.Err('Package not found')

    def get_packages(self):
        with open(path.join(self.pomu_dir, 'world'), 'r') as f:
            lines = [x.strip() for x in f.readlines() if x.strip() != '']
        return lines


def portage_repos():
    """Yield the repositories configured for portage"""
    rsets = portage.db[portage.root]['vartree'].settings.repositories

    for repo in rsets.prepos_order:
        yield repo

def portage_repo_path(repo):
    """Get the path of a given portage repository (repo)"""
    rsets = portage.db[portage.root]['vartree'].settings.repositories

    if repo in rsets.prepos:
        return rsets.prepos[repo].location
    return None

def pomu_status(repo_path):
    """Check if pomu is enabled for a repository at a given path (repo_path)"""
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
        if pomu_status(repo_path):
            return Result.Ok(Repository(repo_path))
        return Result.Err('pomu is not initialized')
    else:
        repo = pomu_active_portage_repo()
        if repo:
            return Result.Ok(Repository(portage_repo_path(repo), repo))
        return Result.Err('pomu is not initialized')

class MergedPackage(Package):
    @property
    def pkgdir(self):
        ret = path.join(self.root, 'metadata', 'pomu', self.category, self.name)
        if self.slot != '0':
            ret = path.join(ret, self.slot)
        return ret

    def patch(self, patch):
        if isinstance(patch, list):
            for x in patch:
                self.patch(x)
            return Result.Ok()
        ps = PatchSet()
        ps.parse(open(patch, 'r'))
        ps.apply(root=self.root)
        self.add_patch(patch)
        return Result.Ok()

    @property
    def patch_list(self):
        with open(path.join(self.pkgdir, 'PATCH_ORDER'), 'r') as f:
            lines = [x.strip() for x in f.readlines() if x.strip() != '']
        return lines

    def add_patch(self, patch, name=None): # patch is a path, unless name is passed
        patch_dir = path.join(self.pkgdir, 'patches')
        makedirs(patch_dir, exist_ok=True)
        if name is None:
            copy2(patch, patch_dir)
            with open(path.join(self.pkgdir, 'PATCH_ORDER'), 'w+') as f:
                f.write(path.basename(patch) + '\n')
        else:
            with open(path.join(patch_dir, name), 'w') as f:
                f.write(patch)
            with open(path.join(self.pkgdir, 'PATCH_ORDER'), 'w+') as f:
                f.write(name + '\n')
