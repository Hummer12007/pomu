"""
A package is a set of files, situated in a root directory.
A package can be installed into a repository.
A package is supposed to be created by a package source from a set of files.
"""

from os import path

from pomu.util.fs import strip_prefix

class Package():
    def __init__(self, name, root, d_path=None, files=None):
        """
        Parameters:
            name - name of the package
            root - root path of the repository (if applicable)
            d_path - a subdirectory of the root path, which would be sourced recursively.
                could be a relative or an absolute path
            files - a set of files to build a package from
        """
        self.name = name
        self.root = root
        self.files = []
        if d_path is None and files is None:
            self.d_path = None
            self.read_path(self.root)
        elif files is None:
            self.d_path = self.strip_root(d_path)
            self.read_path(path.join(self.root, self.d_path))
        elif d_path is None:
            for f in files:
                self.files.append(self.strip_root(f))
        else:
            raise ValueError('You should specify either d_path, or files')

    def strip_root(self, d_path):
            # the path should be either relative, or a child of root
            if d_path.startswith('/'):
                if path.commonprefix(d_path, root) != root:
                    raise ValueError('Path should be a subdirectory of root')
                return strip_prefix(strip_prefix(d_path, root), '/')
            return d_path

    def read_path(self, d_path):
        for wd, dirs, files in os.walk(d_path):
            wd = self.strip_root(wd)
            self.files.extend([(wd, f) for f in files])

