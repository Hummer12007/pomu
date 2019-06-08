"""
A package source module to import packages from filesystem locations (ebuilds)
"""

from os import path

from pomu.package import Package
from pomu.source import dispatcher
from pomu.source.base import PackageBase, BaseSource
from pomu.util.pkg import cpv_split, ver_str
from pomu.util.query import query, QueryContext
from pomu.util.result import Result

class LocalEbuild(PackageBase):
    """A class to represent a local ebuild"""
    __cname__ = 'fs'
    
    def __init__(self, path, category, name, version, slot='0'):
        super().__init__(category, name, version, slot)
        self.path = path

    def fetch(self):
        return Package(self.name, '/', self, self.category, self.version,
                filemap = {
                    path.join(
                        self.category,
                        self.name,
                        '{}/{}-{}.ebuild'.format(self.category, self.name, self.version)
                    ) : self.path})
    
    @staticmethod
    def from_data_dir(pkgdir):
        pkg = PackageBase.from_data_dir(pkgdir)
        if pkg.is_err():
            return pkg
        pkg = pkg.unwrap()

        with QueryContext(category=pkg.category, name=pkg.name, version=pkg.version, slot=pkg.slot):
            with open(path.join(pkgdir, 'FS_ORIG_PATH'), 'r') as f:
                return LocalEbuildSource.parse_ebuild_path(f.readline()).unwrap()

    def write_meta(self, pkgdir):
        super().write_meta(pkgdir)
        with open(path.join(pkgdir, 'FS_ORIG_PATH'), 'w') as f:
            f.write(self.path + '\n')

    def __str__(self):
        return super().__str__() + ' (from {})'.format(self.path)

@dispatcher.source
class LocalEbuildSource(BaseSource):
    """The source module responsible for importing local ebuilds"""
    __cname__ = 'fs'

    @dispatcher.handler(priority=5)
    def parse_ebuild_path(uri):
        if not path.isfile(uri) or not uri.endswith('.ebuild'):
            return Result.Err()
        uri = path.abspath(uri)
        dirn, basen = path.split(uri)
        basen = basen[:-7]
        _, name, v1, v2, v3 = cpv_split(basen)
        ver = ver_str(v1, v2, v3)
        parent = dirn.split('/')[-1]
        # we need to query the impure world
        # TODO: write a global option which would set the impure values non-interactively
        if not ver:
            ver = query('version', 'Please specify package version for {}'.format(basen)).expect()
        category = query('category', 'Please enter category for {}'.format(basen), parent).expect()
        slot = query('slot', 'Please specify package slot', '0').expect()
        return Result.Ok(LocalEbuild(uri, category, name, ver, slot))

    @dispatcher.handler()
    def parse_full(uri):
        if not uri.startswith('fs:'):
            return Result.Err()
        return LocalEbuildSource.parse_ebuild_path(uri[3:])

    @classmethod
    def fetch_package(self, pkg):
        return pkg.fetch()

    @classmethod
    def from_meta_dir(cls, metadir):
        return LocalEbuild.from_data_dir(metadir)
