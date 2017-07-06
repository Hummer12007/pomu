"""
A package source module to import packages from filesystem locations (ebuilds)
"""

from os import path, mkdtemp

from pomu.package import Package
from pomu.source import dispatcher
from pomu.util.pkg import cpv_split, ver_str
from pomu.util.query import query
from pomu.util.result import Result

class Patcher():
    """A class to represent a local ebuild"""
    __name__ = 'patch'
    
    def __init__(self, wrapped, *patches):
        self.patches = patches
        self.wrapped = wrapped
        # nested patching
        if wrapped is Patcher:
            self.patches = wrapped.patches + self.patches
            self.wrapped = wrapped.wrapped

    def fetch(self):
        pkg = self.wrapped.fetch()
        pkg.backend = self
        pd = mkdtemp()
        pkg.merge_into(pd)
        pkg.apply_patches(pd, self.patches)
        return Package(pkg.name, pd, self, pkg.category, pkg.version)
    
    @staticmethod
    def from_data_dir(pkgdir):
        with open(path.join(pkgdir, 'PATCH_ORIG_BACKEND'), 'r') as f:
            wrapped = dispatcher.backends[bname].from_meta_dir(pkgdir)
        patches = [path.join(pkgdir, 'patches', x.strip())
                for x in open(path.join(pkgdir, 'PATCH_PATCHES_ORDER'))]

    def write_meta(self, pkgdir):
        with open(path.join(pkgdir, 'PATCH_ORIG_BACKEND'), 'w') as f:
            f.write('{}\n'.format(self.wrapped.__name__))
        with open(path.join(pkgdir, 'PATCH_PATCHES_ORDER'), 'w') as f:
            for p in self.patches:
                f.write(path.basename(p) + '\n')
        os.makedirs(path.join(pkgdir, 'patches'), exist_ok=True)
        for p in self.patches:
            shutil.copy2(p, path.join(pkgdir, 'patches'))
        # write originals?

    def __str__(self):
        return '{}/{}-{} (from {})'.format(self.category, self.name, self.version, self.path)

@dispatcher.source
class LocalEbuildSource():
    """The source module responsible for importing and patching various ebuilds"""
    @dispatcher.handler()
    def parse_full(uri):
        if not uri.startswith('patch:'):
            return Result.Err()
        uri = uri[6:]
        patchf, _, pks = uri.partition(':')
        if not path.isfile(patchf):
            return Result.Err('Invalid patch file')
        if not pks:
            return Result.Err('Package not provided')
        pkg = dispatcher.get_package(pks)
        return Result.Ok(Patcher(patchf, pkg)

    @classmethod
    def from_meta_dir(cls, metadir):
        return Patcher.from_data_dir(cls, metadir)
