"""
A package source module to import ebuilds and patches from bugzilla
"""

import xmlrpc.client
from os import path
from urllib.parse import urlparse

from pomu.package import Package
from pomu.source import dispatcher
from pomu.source.base import PackageBase, BaseSource
from pomu.util.iquery import EditSelectPrompt
from pomu.util.misc import extract_urls
from pomu.util.query import query, QueryContext
from pomu.util.result import Result

class BzEbuild(PackageBase):
    """A class to represent an ebuild from bugzilla"""
    __cname__ = 'bugzilla'

    def __init__(self, bug_id, filemap, category, name, version, slot='0'):
        super().__init__(category, name, version, slot)
        self.bug_id = bug_id
        self.filemap = filemap

    def fetch(self):
        return Package(self.name, '/', self, self.category, self.version, filemap=self.filemap)

    @staticmethod
    def from_data_dir(pkgdir):
        pkg = PackageBase.from_data_dir(pkgdir)
        if pkg.is_err():
            return pkg
        pkg = pkg.unwrap()

        with QueryContext(category=pkg.category, name=pkg.name, version=pkg.version, slot=pkg.slot):
            with open(path.join(pkgdir, 'BZ_BUG_ID'), 'r') as f:
                return BugzillaSource.parse_bug(f.readline()).unwrap()

    def write_meta(self, pkgdir):
        super().write_meta(pkgdir)
        with open(path.join(pkgdir, 'BZ_BUG_ID'), 'w') as f:
            f.write(self.bug_id + '\n')

    def __str__(self):
        return super().__str__() + ' (from bug {})'.format(self.bug_id)

CLIENT_BASE = 'https://bugs.gentoo.org/xmlrpc.cgi'

@dispatcher.source
class BugzillaSource(BaseSource):
    """The source module responsible for importing ebuilds and patches from bugzilla tickets"""
    __cname__ = 'bugzilla'

    @dispatcher.handler(priority=1)
    @staticmethod
    def parse_bug(uri):
        if not uri.isdigit():
            return Result.Err()
        uri = int(uri)
        proxy = xmlrpc.client.ServerProxy(CLIENT_BASE).Bug
        payload = {'ids': [uri]}
        try:
            proxy.get(payload)
        except (xmlrpc.client.Fault, OverflowError) as err:
            return Result.Err(str(err))
        attachments = proxy.attachments(payload)['bugs'][str(uri)]
        comments = proxy.comments(payload)['bugs'][str(uri)]['comments']
        comment_links = []
        for comment in comments:
            comment_links.extend(extract_urls(comment['text']))
        items = [(x['file_name'], x['data'].data.decode('utf-8')) for x in attachments] + comment_links
        if not items:
            return Result.Err()
        p = EditSelectPrompt(items)
        files = p.run()
        if not files:
            return Result.Err()
        category = query('category', 'Please enter package category').expect()
        name = query('name', 'Please enter package name').expect()
        ver = query('version', 'Please specify package version for {}'.format(name)).expect()
        slot = query('slot', 'Please specify package slot', '0').expect()
        fmap = {path.join(category, name, x[2]): x[1] for x in files}
        return Result.Ok(BzEbuild(uri, fmap, category, name, ver, slot))

    @dispatcher.handler(priority=2)
    @staticmethod
    def parse_link(uri):
        res = urlparse(uri)
        if res.netloc != 'bugs.gentoo.org':
            return Result.Err()
        if res.path == '/show_bugs.cgi':
            ps = [x.split('=') for x in res.params.split('&') if x.startswith('id=')][1]
            return BugzillaSource.parse_bug(ps)
        if res.path.lstrip('/').isdigit():
            return BugzillaSource.parse_bug(res.path.lstrip('/'))
        return Result.Err()


    @dispatcher.handler()
    @staticmethod
    def parse_full(uri):
        if not uri.startswith('bug:'):
            return Result.Err()
        rem = uri[4:]
        if rem.isdigit():
            return BugzillaSource.parse_bug(rem)
        return BugzillaSource.parse_link(rem)

    @classmethod
    def fetch_package(self, pkg):
        return pkg.fetch()

    @classmethod
    def from_meta_dir(cls, metadir):
        return BzEbuild.from_data_dir(metadir)
