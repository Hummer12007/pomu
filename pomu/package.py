"""
A package is a set of files, situated in a root directory.
A package can be installed into a repository.
A package is supposed to be created by a package source from a set of files.
"""

from os import path

from portage.util.string import strip_prefix

class Package():
    def __init__(self, name, path):
        self.name = name
        self.root = path
        self.read_files(files)

    #todo: file sets
    def read_files(self)
        self.files = []
        for wd, dirs, files in os.walk(path):
            wd = strip_prefix(strip_prefix(wd, path), '/')
            self.files.extend([(wd, f) for f in files])

