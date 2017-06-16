"""
A package source module to import packages from configured portage repositories
"""
import os
import re

from functools import cmp_to_key
from os import path

from portage.versions import best, suffix_value, vercmp

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

    def fetch(self):
        return Package(self.name, portage_repo_path(self.repo),
                files=[path.join(self.category, self.name, 'metadata.xml'),
                    path.join(self.category, self.name, self.name + '-' + self.version + '.ebuild')])

suffixes = [x[0] for x in sorted(suffix_value.items(), key=lambda x:x[1])]
misc_dirs = ['profiles', 'licenses', 'eclass', 'metadata', 'distfiles', 'packages', 'scripts'. '.git']

@dispatcher.source
class PortageSource():
    @dispatcher.handler(priority=5)
    def parse_spec(uri, repo=None):
        # dev-libs/openssl-0.9.8z_p8-r100:0.9.8::gentoo
        pkg, _, repo_ = uri.partition('::') # portage repo may be specified on the rhs as well
        if repo_:
            repo = repo_
        # dev-libs/openssl-0.9.8z_p8-r100:0.9.8
        pkg, _, slot = uri.partition(':') # slot may be omitted
        if not slot:
            slot = None
        category, name, vernum, suff, rev = cpv_split(pkg)
        res = sanity_check(repo, category, name, vernum, suff, rev, slot)
        if not res:
            return Result.Err()
        return Result.Ok(res)

    def cpv_split(pkg):
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
        return category, name, vernum, suff, rev


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
        return parse_spec(uri, repo)

    def sanity_check(repo, category, name, vernum, suff, rev, slot):
        if not name:
            return False
        if repo and repo not in list(portage_repos()):
            return False
        if (rev or suff) and not vernum:
            return False
        if vernum:
            ver = ver_str(vernum, suff, rev)
        else:
            ver = None
        pkgs = repo_pkgs(repo, category, name, ver, slot)
        if not pkgs:
            return False
        pkg = sorted(pkgs, key=cmp_to_key(lambda x,y:vercmp(x[3],y[3])), reverse=True)[0]
        return PortagePackage(*pkg)


    def ver_str(vernum, suff, rev):
        return vernum + (suff if suff else '') + (rev if rev else '')

    def best_ver(repo, category, name, ver=None):
        """Gets the best (newest) version of a package  in the repo"""
        ebuilds = [category + '/' + name + x[len(name):-6] for x in
                os.listdir(path.join(portage_repo_path(repo)), category, name)
                if x.endswith('.ebuild')]
        cat, name, vernum, suff, rev = cpv_split(best(ebuilds))
        return ver_str(vernum, suff, rev)

    def repo_pkgs(repo, category, name, ver=None, slot=None):
        """List of package occurences in the repo"""
        if not repo:
            res = []
            for r in portage_repos():
                res.extend(repo_pkgs(r, category, name, ver, slot))
            return res
        if category:
            if path.exists(path.join(portage_repo_path(repo), category, name)):
                return [(repo, category, name, best_ver(repo, category, name))]
            return []
        rpath = portage_repo_path(repo)
        dirs = set(os.listdir(rpath)) - set(misc_dirs)
        res = []
        for d in dirs:
            if path.isdir(path.join(rpath, d, name)):
                res.append((repo, d, name, best_ver(repo, d, name)))
        return res
