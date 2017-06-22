"""
A package is a set of files, situated in a root directory.
A package can be installed into a repository.
A package is supposed to be created by a package source from a set of files.
"""

from os import path, walk, makedirs
from shutil import copy2

import subprocess

from pomu.util.fs import strip_prefix
from pomu.util.result import Result

class Package():
    def __init__(self, name, root, category=None, version=None, slot='0', d_path=None, files=None):
        """
        Parameters:
            name - name of the package
            root - root path of the repository (if applicable)
            d_path - a subdirectory of the root path, which would be sourced recursively.
                could be a relative or an absolute path
            files - a set of files to build a package from
            category, version, slot - self-descriptive
        """
        self.name = name
        self.root = root
        self.category = category
        self.version = version
        self.slot = slot
        self.files = []
        if d_path is None and files is None:
            self.d_path = None
            self.read_path(self.root)
        elif files is None:
            self.d_path = self.strip_root(d_path)
            self.read_path(path.join(self.root, self.d_path))
        elif d_path is None:
            for f in files:
                self.files.append(path.split(self.strip_root(f)))
        else:
            raise ValueError('You should specify either d_path, or files')

    def strip_root(self, d_path):
        """Strip the root component of a path"""
        # the path should be either relative, or a child of root
        if d_path.startswith('/'):
            if path.commonprefix(d_path, self.root) != self.root:
                raise ValueError('Path should be a subdirectory of root')
            return strip_prefix(strip_prefix(d_path, self.root), '/')
        return d_path

    def read_path(self, d_path):
        """Recursively add files from a subtree"""
        for wd, dirs, files in walk(d_path):
            wd = self.strip_root(wd)
            self.files.extend([(wd, f) for f in files])

    def merge_into(self, dst):
        """Merges contents of the package into a specified directory"""
        for wd, f in self.files:
            dest = path.join(dst, wd)
            try:
                makedirs(dest, exist_ok=True)
                copy2(path.join(self.root, wd, f), dest)
            except PermissionError:
                return Result.Err('You do not have enough permissions')
        return Result.Ok()

    def gen_manifests(self, dst):
        """
        Generate manifests for the installed package.
        TODO: use portage APIs instead of calling repoman.
        """
        dirs = [x for wd, f in self.files if y.endswith('.ebuild')]
        dirs = list(set(dirs))
        res = []
        for d_ in dirs:
            d = path.join(dst, d)
            ret = subprocess.run(['repoman', 'manifest'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    cwd=d)
            if r != 0:
                return Result.Err('Failed to generate manifest at', d)
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
