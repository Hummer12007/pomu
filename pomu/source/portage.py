"""
A package source module to import packages from configured portage repositories
"""
import os
import re

from os import path

from pomu.repo.repo import portage_repos
from pomu.source import dispatcher
from pomu.util import Result
from pomu.util.str import pivot

class PortagePackage():
    """A class to represent a portage package"""
    def __init__(self, repo, category, name, version, slot='0'):
        self.repo = repo
        self.category = category
        self.name = name
        self.version = version
        self.slot = slot

suffixes = ['alpha', 'beta', 'pre', 'rc', 'p']
misc_dirs = ['profiles', 'licenses', 'eclass', 'metadata', 'distfiles', 'packages', 'scripts'. '.git']

@dispatcher.source
class PortageSource():
    @dispatcher.handler()
    def parse_full(uri):
        # portage/gentoo:dev-libs/openssl-0.9.8z_p8-r100:0.9.8::gentoo
        if not uri.startswith('portage')
            return Result.Err()
        uri = uri[len('portage'):]
        # gentoo:dev-libs/openssl-0.9.8z_p8-r100:0.9.8::gentoo
        if uri.startswith('/'): # repo may be omitted
            repo, _, uri_  = uri[1:].partition(':')
            if uri_ == uri[1:]:
                return Result.Err()
            uri = uri_
        elif uri.startswith(':'):
            repo = None
            uri = uri[1:]
        # dev-libs/openssl-0.9.8z_p8-r100:0.9.8::gentoo
        pkg, _, repo_ = uri.partition('::') # portage repo may be specified on the rhs as well
        if repo_:
            repo = repo
        # dev-libs/openssl-0.9.8z_p8-r100:0.9.8
        pkg, _, slot = uri.partition(':') # slot may be omitted
        if not slot:
            slot = None
        # dev-libs/openssl-0.9.8z_p8-r100
        category, _, pkg = pkg.rpartition('/') # category may be omitted
        # openssl-0.9.8z_p8-r100
        m = re.search(r'-r\d+$', pkg) # revision is optional
        if m:
            pkg, rev = pivot(pkg, m.start(0))
        else:
            rev = None
        # openssl-0.9.8z_p8
        m = re.search(r'_({})(\d*)$'.format('|'.join(suffixes)))
        if m:
            pkg, suff = pivot(pkg, m.start(0))
        else:
            suff = None
        # openssl-0.9.8z
        m = re.search(r'-(\d+(\.\d+)*)([a-z])?$')
        if m:
            pkg, vernum = pivot(pkg, m.start(0))
        else:
            vernum = None
        # openssl
        name = pkg

    def sanity_check(repo, category, name, vernum, suff, rev, slot):
        if not name:
            return False
        if repo and repo not in list(portage_repos()):
            return False
        if (rev or suff) and not vernum:
            return False
        if vernum:
            ver = vernum + (suff if suff else '') + (rev if rev else '')
        else:
            ver = None
        if not repo_pkgs(repo, category, name, ver, slot):
            return False

    # TODO: vvv
    def pkg_slot(repo, category, name, ver):

    def best_ver(repo, category, name, ver, slot):
        """Gets the best (newest) version of a package matching slot in the repo"""
        ebuilds = [x[:-6] for x in
                os.listdir(path.join(portage_repo_path(repo)), category, name)
                if x.endswith('.ebuild')]

    def repo_pkgs(repo, category, name, ver, slot):
        """List of package occurences in the repo"""
        if not repo:
            res = []
            for r in portage_repos():
                res.extend(has_pkg(r, category, name))
            return res
        if category:
            if path.exists(path.join(portage_repo_path(repo), category, name)):
                return [(repo, category, name)]
            return []
        rpath = portage_repo_path(repo)
        dirs = set(os.listdir(rpath)) - set(misc_dirs)
        res = []
        for d in dirs:
            if path.isdir(path.join(rpath, d, name)):
                res.append(repo, d, name)
        return res
