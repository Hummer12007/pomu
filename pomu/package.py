"""
A package is a set of files, situated in a root directory.
A package can be installed into a repository.
A package is supposed to be created by a package source from a set of files.
A package is supposed to know, where it came from.
"""

from os import path, walk, makedirs
from shutil import copy2

import subprocess

from patch import PatchSet

from pomu.util.fs import strip_prefix
from pomu.util.misc import list_add
from pomu.util.result import Result

class Package():
    def __init__(self, name, root, backend=None, category=None, version=None, slot='0', d_path=None, files=None, filemap=None, patches=[]):
        """
        Parameters:
            backend - specific source module object/class
            name - name of the package
            root - root path of the repository (if applicable)
            d_path - a subdirectory of the root path, which would be sourced recursively.
                could be a relative or an absolute path
            files - a set of files to build a package from
            filemap - a mapping from destination files to files in the filesystem
            category, version, slot - self-descriptive
        """
        self.backend = backend
        self.name = name
        self.root = root
        self.category = category
        self.version = version
        self.slot = slot
        self.filemap = {}
        self.patches = patches
        if d_path is None and files is None and filemap is None:
            self.d_path = None
            self.read_path(self.root)
        elif d_path:
            self.d_path = self.strip_root(d_path)
            self.read_path(path.join(self.root, self.d_path))
        elif files:
            for f in files:
                dst = self.strip_root(f)
                self.filemap[dst] = path.join(self.root, dst)
        elif filemap:
            self.filemap = filemap
        else:
            raise ValueError('You should specify either d_path, files or filemap')

    @property
    def files(self):
        res = []
        for k in self.filemap:
            res.append(path.split(k))
        return res

    @property
    def ebuild_path(self):
        return path.join(self.category, self.name, '{}-{}.ebuild'.format(self.name, self.version))

    def strip_root(self, d_path):
        """Strip the root component of d_path"""
        # the path should be either relative, or a child of root
        if d_path.startswith('/'):
            if path.commonprefix([d_path, self.root]) != self.root:
                raise ValueError('Path should be a subdirectory of root')
            return strip_prefix(strip_prefix(d_path, self.root), '/')
        return d_path

    def read_path(self, d_path):
        """Recursively add files from a subtree (specified by d_path)"""
        for wd, dirs, files in walk(d_path):
            wd = self.strip_root(wd)
            self.filemap.update({path.join(wd, f): path.join(self.root, wd, f) for f in files})

    def merge_into(self, dst):
        """Merges contents of the package into a specified directory (dst)"""
        for trg, src in self.filemap.items():
            wd, filename = path.split(trg)
            dest = path.join(dst, wd)
            try:
                makedirs(dest, exist_ok=True)
                if isinstance(src, bytes):
                    with open(path.join(dest, filename), 'wb') as f:
                        f.write(src)
                else:
                    copy2(src, dest)
            except PermissionError:
                return Result.Err('You do not have enough permissions')
        return Result.Ok().and_(self.apply_patches())

    def patch(self, patch):
        if patch:
            list_add(self.patches, patch)

    def apply_patches(self, revert=False):
        """Applies a sequence of patches at the root (after merging)"""
        ps = PatchSet()
        for p in self.patches:
            ps.parse(open(p, 'r'))
        for patch in ps:
            if '.ebuild' in ps.target:
                ps.source = self.ebuild_path
                ps.target = self.ebuild_path
            elif '/files/' in ps.target:
                comps = ps.target.split('/')
                comps = [self.category, self.name] + comps[comps.index('files'):]
                ps.target = '/'.join(comps)
                if not ps.source.split('/'[-2:] == ['dev', 'null']):
                    ps.source = '/'.join(comps)
            else:
                pass

        if revert:
            ps.revert(root=self.root)
        else:
            ps.apply(root=self.root)
        return Result.Ok()

    def gen_manifests(self, dst):
        """
        Generate manifests for the installed package (in the dst directory).
        TODO: use portage APIs instead of calling repoman.
        """
        dirs = [wd for wd, f in self.files if f.endswith('.ebuild')]
        dirs = list(set(dirs))
        res = []
        for d_ in dirs:
            d = path.join(dst, d_)
            ret = subprocess.run(['repoman', 'manifest'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    cwd=d)
            if ret.returncode != 0:
                return Result.Err('Failed to generate manifest at ' + d)
            if path.exists(path.join(d, 'Manifest')):
                res.append(path.join(d, 'Manifest'))
        return Result.Ok(res)


    def __str__(self):
        s = ''
        if self.category:
            s = self.category + '/'
        s += self.name
        if self.version:
            s += '-' + self.version
        if self.slot != '0':
            s += self.slot
        return s

class PatchList():
    """A class to represent a sequence of patches (can be merged in the repo)"""
    def __init__(self, category, name, version, patches, slot='0'):
        self.category = category
        self.name = name
        self.version = version
        self.slot = slot
        self.patches = patches
