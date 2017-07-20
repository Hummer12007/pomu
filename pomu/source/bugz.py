"""
A package source module to import ebuilds and patches from bugzilla
"""

import xmlrpc.client
from os import path
from urllib.parse import urlparse

from pbraw import grab

from pomu.package import Package
from pomu.source import dispatcher
from pomu.util.misc import extract_urls, parse_range
from pomu.util.pkg import cpv_split, ver_str
from pomu.util.query import query, QueryContext
from pomu.util.result import Result

class BzEbuild():
    """A class to represent a local ebuild"""
    __name__ = 'fs'

    # slots?
    def __init__(self, bug_id, category, name, version, filemap):
        self.bug_id = bug_id
        self.category = category
        self.name = name
        self.version = version
        self.filemap = filemap

    def fetch(self):
        return Package(self.name, '/', self, self.category, self.version, self.filemap)

    @staticmethod
    def from_data_dir(pkgdir):
        with open(path.join(pkgdir, 'BZ_BUG_ID'), 'r') as f:
            return BugzillaSource.parse_bug(f.readline()).unwrap()

    def write_meta(self, pkgdir):
        with open(path.join(pkgdir, 'BZ_BUG_ID'), 'w') as f:
            f.write(self.bug_id + '\n')

    def __str__(self):
        return '{}/{}-{} (from {})'.format(self.category, self.name, self.version, self.path)

CLIENT_BASE = 'https://bugs.gentoo.org/xmlrpc.cgi'

@dispatcher.source
class BugzillaSource():
    """The source module responsible for importing ebuilds and patches from bugzilla tickets"""
    @dispatcher.handler(priority=1)
    def parse_bug(uri):
        if not uri.isdigit():
            return Result.Err()
        uri = int(uri)
        proxy = xmlrpc.client.ServerProxy(CLIENT_BASE).Bug
        payload = {'ids': [uri]}
        try:
            bug = proxy.get(payload)
        except (xmlrpc.client.Fault, OverflowError) as err:
            return Result.Err(str(err))
        attachments = proxy.attachments(payload)['bugs'][str(uri)]
        comments = proxy.comments(payload)['bugs'][str(uri)]['comments']
        comment_links = []
        for comment in comments:
            comment_links.extend(extract_urls(text))
        items = attachments + comment_links
        if not items:
            return Result.Err()
        lines = ['Please select required items (ranges are accepted)']
        for idx, item in enumerate(items):
            if isinstance(item, str):
                lines.append('{} - {}'.format(idx, item))
            else:
                lines.append('{} - Attachment: {}'.format(idx, item['file_name']))
        lines.append('>>> ')
        rng = query('items', '\n'.join(lines), 1)
        idxs = parse_range(rng, len(items))
        if not idxs:
            return Result.Err()
        filtered = [x for idx, x in enumerate(items) if idx in idxs]
        files = []
        for idx, item in enumerate(idxs):
            if isinstance(item, str):
                files.extend([(x[0], x[1].encode('utf-8')) for x in grab(item)])
            else:
                files.append((item['file_name'], item['data']))
        if not files:
            return Result.Err()
        category = query('category', 'Please enter package category').expect()
        name = query('name', 'Please enter package name')
        ver = query('version', 'Please specify package version for {}'.format(name)).expect()
        # TODO: ???
        fmap = {}
        for fn, data in files:
            with QueryContext(path=None):
                fpath = query('path', 'Please enter path for {} file'.format(fn), path.join(category, name, fn))
                fmap[fpath] = data



        return Result.Ok(BzEbuild(uri, category, name, ver, uri))

    @dispatcher.handler(priority=2)
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
    def parse_full(uri):
        if not uri.startswith('bug:'):
            return Result.Err()
        rem = uri[4:]
        if rem.isdigit():
            return BugzillaSource.parse_bug(rem)
        return BugzillaSource.parse_link(rem)

    @classmethod
    def from_meta_dir(cls, metadir):
        return BzEbuild.from_data_dir(cls, metadir)
