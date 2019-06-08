"""
A package source module to import packages from configured portage repositories
"""
from functools import cmp_to_key
from os import path

from portage.versions import vercmp

from pomu.package import Package
from pomu.repo.repo import portage_repos, portage_repo_path
from pomu.source import dispatcher
from pomu.source.base import PackageBase, BaseSource
from pomu.util.pkg import cpv_split, ver_str
from pomu.util.portage import repo_pkgs
from pomu.util.result import Result

class PortagePackage(PackageBase):
    """A class to represent a portage package"""
    __cname__ = 'portage'

    def __init__(self, repo, category, name, version, slot='0'):
        super().__init__(category, name, version, slot)
        self.repo = repo

    def fetch(self):
        return Package(self.name, portage_repo_path(self.repo), self,
                category=self.category, version=self.version, slot=self.slot,
                files=[path.join(self.category, self.name, 'metadata.xml'),
                    path.join(self.category, self.name, self.name + '-' + self.version + '.ebuild')])

    def write_meta(self, pkgdir):
        super().write_meta(pkgdir)
        with open(path.join(pkgdir, 'PORTAGE_DATA'), 'w') as f:
            f.write(self.repo + '\n')

    @staticmethod
    def from_data_dir(pkgdir):
        pkg = PackageBase.from_data_dir(pkgdir)
        if pkg.is_err():
            return pkg
        pkg = pkg.unwrap()

        with open(path.join(pkgdir, 'PORTAGE_DATA'), 'r') as f:
            repo = f.readline()
        if sanity_check(repo, pkg.category, pkg.name, None, None, None, pkg.slot, ver=pkg.version):
            return Result.Ok(PortagePackage(repo, pkg.category, pkg.name, pkg.slot, pkg.version))
        return Result.Err('Package {} not found'.format(pkg))

    def __str__(self):
        return super().__str__() + '::' + self.repo


@dispatcher.source
class PortageSource(BaseSource):
    """The source module responsible for fetching portage packages"""
    __cname__ = 'portage'

    @dispatcher.handler(priority=5)
    def parse_spec(uri, repo=None):
        # dev-libs/openssl-0.9.8z_p8-r100:0.9.8::gentoo
        pkg, _, repo_ = uri.partition('::') # portage repo may be specified on the rhs as well
        if repo_:
            repo = repo_
        # dev-libs/openssl-0.9.8z_p8-r100:0.9.8
        pkg, _, slot = uri.partition(':') # slot may be omitted
        if not slot:
            slot = None
        category, name, vernum, suff, rev = cpv_split(pkg)
        res = sanity_check(repo, category, name, vernum, suff, rev, slot)
        if not res:
            return Result.Err()
        return Result.Ok(res)

    @dispatcher.handler()
    def parse_full(uri):
        # portage/gentoo:dev-libs/openssl-0.9.8z_p8-r100:0.9.8::gentoo
        if not uri.startswith('portage'):
            return Result.Err()
        uri = uri[len('portage'):]
        # gentoo:dev-libs/openssl-0.9.8z_p8-r100:0.9.8::gentoo
        if uri.startswith('/'): # repo may be omitted
            repo, _, uri_  = uri[1:].partition(':')
            if uri_ == uri[1:]:
                return Result.Err()
            uri = uri_
        elif uri.startswith(':'):
            repo = None
            uri = uri[1:]
        return PortageSource.parse_spec(uri, repo)

    @dispatcher.handler(priority=4)
    def parse_repo_ebuild(uri):
        if not path.exists(uri):
            return Result.Err()
        uri = path.abspath(uri)
        prefixes = [(x, portage_repo_path(x)) for x in portage_repos()]
        for repo, repo_path in prefixes:
            repo_path = repo_path.rstrip('/') + '/'
            if uri.startswith(repo):
                if path.isfile(uri):
                    if not uri.endswith('.ebuild'):
                        return Result.Err()
                    _, name, v1, v2, v3 = cpv_split(path.basename(uri))
                    ver = ver_str(v1, v2, v3)
                    dircomps = path.dirname(uri)[len(repo_path):].split('/')
                    if len(dircomps) != 2:
                        return Result.Err()
                    return PortageSource.parse_spec('{}/{}-{}::{}'.format(dircomps[0], name, ver, repo))
                elif path.isdir(uri):
                    dircomps = path.dirname(uri)[len(repo_path):].split('/')
                    if len(dircomps) != 2:
                        return Result.Err()
                    return PortageSource.parse_spec('{}/{}'.format(*dircomps))
            return Result.Err()


    @classmethod
    def fetch_package(cls, pkg):
        return pkg.fetch()

    @classmethod
    def from_meta_dir(cls, metadir):
        return PortagePackage.from_data_dir(metadir)


def sanity_check(repo, category, name, vernum, suff, rev, slot, ver=None):
    """
    Checks whether a package descriptor is valid and corresponds
    to a package in a configured portage repository
    """
    if not name:
        return False
    if repo and repo not in list(portage_repos()):
        return False
    if not ver:
        if (rev or suff) and not vernum:
            return False
        if vernum:
            ver = ver_str(vernum, suff, rev)
        else:
            ver = None
    pkgs = repo_pkgs(repo, category, name, ver, slot)
    if not pkgs:
        return False
    pkg = sorted(pkgs, key=cmp_to_key(lambda x,y:vercmp(x[3],y[3])), reverse=True)[0]
    return PortagePackage(*pkg)

__all__ = ['PortagePackage', 'PortageSource']
