"""
A package source module to import packages from URLs
"""

from os import path

from pbraw import grab

from pomu.package import Package
from pomu.source import dispatcher
from pomu.source.base import PackageBase, BaseSource
from pomu.util.query import query
from pomu.util.result import Result

class URLEbuild(PackageBase):
    """A class to represent an ebuild fetched from a url"""
    __name__ = 'fs'
    
    def __init__(self, category, name, version, url, contents=None):
        self.category = category
        self.name = name
        self.version = version
        self.url = url
        self.contents = contents

    def fetch(self):
        if self.contents:
            if isinstance(self.contents, str):
                self.content = self.content.encode('utf-8')
        else:
            fs = grab(self.url)
            self.content = fs[0][1].encode('utf-8')
        return Package(self.name, '/', self, self.category, self.version,
                filemap = {
                    path.join(
                        self.category,
                        self.name,
                        '{}/{}-{}.ebuild'.format(self.category, self.name, self.version)
                    ) : self.content})
    
    @staticmethod
    def from_data_dir(pkgdir):
        with open(path.join(pkgdir, 'ORIG_URL'), 'r') as f:
            return URLGrabberSource.parse_link(f.readline()).unwrap()

    def write_meta(self, pkgdir):
        with open(path.join(pkgdir, 'ORIG_URL'), 'w') as f:
            f.write(self.path + '\n')

    def __str__(self):
        return '{}/{}-{} (from {})'.format(self.category, self.name, self.version, self.path)

@dispatcher.source
class URLGrabberSource(BaseSource):
    """
    The source module responsible for grabbing modules from URLs,
    including pastebins
    """
    @dispatcher.handler(priority=5)
    def parse_link(uri):
        if not (uri.startswith('http://') or uri.startswith('https://')):
            return Result.Err()

        name = query('name', 'Please specify package name'.expect())
        category, _, name = name.rpartition('/')
        ver = query('version', 'Please specify package version for {}'.format(name)).expect()
        if not category:
            category = query('category', 'Please enter category for {}'.format(name)).expect()
        files = grab(uri)
        if not files:
            return Result.Err()
        return Result.Ok(URLEbuild(category, name, ver, uri, files[0][1]))

    @dispatcher.handler()
    def parse_full(url):
        if not url.startswith('url:'):
            return Result.Err()
        return URLGrabberSource.parse_ebuild_path(url[4:])

    @classmethod
    def from_meta_dir(cls, metadir):
        return URLEbuild.from_data_dir(cls, metadir)
