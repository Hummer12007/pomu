"""
A package source module to import packages from URLs
"""

from os import path

from pbraw import grab

from pomu.package import Package
from pomu.source import dispatcher
from pomu.source.base import PackageBase, BaseSource
from pomu.util.query import query, QueryContext
from pomu.util.result import Result

class URLEbuild(PackageBase):
    """A class to represent an ebuild fetched from a url"""
    __cname__ = 'url'
    
    def __init__(self, url, contents, category, name, version, slot):
        self.url = url
        self.contents = contents
        self.category = category
        self.name = name
        self.version = version
        self.slot = slot

    def fetch(self):
        if self.contents:
            if isinstance(self.contents, str):
                self.content = self.contents.encode('utf-8')
        else:
            fs = grab(self.url)
            self.content = fs[0][1].encode('utf-8')
        return Package(self.name, '/', self, self.category, self.version,
                filemap = {
                    path.join(
                        self.category,
                        self.name,
                        '{}-{}.ebuild'.format(self.name, self.version)
                    ) : self.content})
    
    @staticmethod
    def from_data_dir(pkgdir):
        pkg = PackageBase.from_data_dir(pkgdir)
        if pkg.is_err():
            return pkg
        pkg = pkg.unwrap()

        with QueryContext(category=pkg.category, name=pkg.name, version=pkg.version, slot=pkg.slot):
            with open(path.join(pkgdir, 'ORIG_URL'), 'r') as f:
                return URLGrabberSource.parse_link(f.readline()).unwrap()

    def write_meta(self, pkgdir):
        super().write_meta(pkgdir)
        with open(path.join(pkgdir, 'ORIG_URL'), 'w') as f:
            f.write(self.path + '\n')

    def __str__(self):
        return super().__str__() + ' (from {})'.format(self.url)

@dispatcher.source
class URLGrabberSource(BaseSource):
    """
    The source module responsible for grabbing modules from URLs,
    including pastebins
    """
    __cname__ = 'url'

    @dispatcher.handler(priority=5)
    def parse_link(uri):
        if not (uri.startswith('http://') or uri.startswith('https://')):
            return Result.Err()

        name = query('name', 'Please specify package name').expect()
        category, _, name = name.rpartition('/')
        ver = query('version', 'Please specify package version for {}'.format(name)).expect()
        if not category:
            category = query('category', 'Please enter category for {}'.format(name)).expect()
        files = grab(uri)
        if not files:
            return Result.Err()
        slot = query('slot', 'Please specify package slot', '0').expect()
        return Result.Ok(URLEbuild(uri, files[0][1], category, name, ver, slot))

    @dispatcher.handler()
    def parse_full(url):
        if not url.startswith('url:'):
            return Result.Err()
        return URLGrabberSource.parse_ebuild_path(url[4:])

    @classmethod
    def fetch_package(self, pkg):
        return pkg.fetch()

    @classmethod
    def from_meta_dir(cls, metadir):
        return URLEbuild.from_data_dir(cls, metadir)
