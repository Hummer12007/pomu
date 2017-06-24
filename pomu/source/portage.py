"""
A package source module to import packages from configured portage repositories
"""
import os
import re

from functools import cmp_to_key
from os import path

from portage.versions import best, suffix_value, vercmp

from pomu.package import Package
from pomu.repo.repo import portage_repos, portage_repo_path
from pomu.source import dispatcher
from pomu.util.result import Result
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
        return Package(self, self.name, portage_repo_path(self.repo),
                category=self.category, version=self.version, slot=self.slot,
                files=[path.join(self.category, self.name, 'metadata.xml'),
                    path.join(self.category, self.name, self.name + '-' + self.version + '.ebuild')])

    def write_meta(self, pkgdir):
        with open(path.join(pkgdir, 'PORTAGE_DATA'), 'w') as f:
            f.write(self.repo + '\n')
            f.write(self.category + '\n')
            f.write(self.name + '\n')
            f.write(self.version + '\n')
            f.write(self.slot + '\n')

    @staticmethod
    def from_data_file(path):
        try:
            lines = [x.strip() for x in open(path, 'r')]
        except:
            return Result.Err('Could not read data file')
        if len(lines) < 5:
            return Result.Err('Invalid data provided')
        res = PortagePackage()
        res.repo, res.category, res.name, res.version, res.slot, *_ = lines
        if sanity_check(res.repo, res.category, res.name, None, None, None, res.slot, ver=res.version):
            return Result.Ok(res)
        return Result.Err('Package {} not found'.format(res))

    def __str__(self):
        return '{}/{}-{}{}::{}'.format(self.category, self.name, self.version,
                '' if self.slot == '0' else ':' + self.slot, self.repo)

suffixes = [x[0] for x in sorted(suffix_value.items(), key=lambda x:x[1])]
misc_dirs = ['profiles', 'licenses', 'eclass', 'metadata', 'distfiles', 'packages', 'scripts', '.git']

@dispatcher.source
class PortageSource():
    """The source module responsible for fetching portage packages"""
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

    @dispatcher.handler()
    def parse_full(uri):
        # portage/gentoo:dev-libs/openssl-0.9.8z_p8-r100:0.9.8::gentoo
        if not uri.startswith('portage'):
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

    @classmethod
    def fetch_package(cls, pkg):
        return pkg.fetch()


def sanity_check(repo, category, name, vernum, suff, rev, slot, ver=None):
    """
    Checks whether a package descriptor is valid and corresponds
    to a package in a configured portage repository
    """
    if not name:
        return False
    if repo and repo not in list(portage_repos()):
        return False
    if not ver:
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
    """Gets the string representation of the version"""
    return vernum + (suff if suff else '') + (rev if rev else '')

def best_ver(repo, category, name, ver=None):
    """Gets the best (newest) version of a package in the repo"""
    ebuilds = [category + '/' + name + x[len(name):-7] for x in
            os.listdir(path.join(portage_repo_path(repo), category, name))
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

def cpv_split(pkg):
    # dev-libs/openssl-0.9.8z_p8-r100
    category, _, pkg = pkg.rpartition('/') # category may be omitted
    # openssl-0.9.8z_p8-r100
    m = re.search(r'-r\d+$', pkg) # revision is optional
    if m:
        pkg, rev = pivot(pkg, m.start(0), False)
    else:
        rev = None
    # openssl-0.9.8z_p8
    m = re.search(r'_({})(\d*)$'.format('|'.join(suffixes)), pkg)
    if m:
        pkg, suff = pivot(pkg, m.start(0), False)
    else:
        suff = None
    # openssl-0.9.8z
    m = re.search(r'-(\d+(\.\d+)*)([a-z])?$', pkg)
    if m:
        pkg, vernum = pivot(pkg, m.start(0), False)
    else:
        vernum = None
    # openssl
    name = pkg
    return category, name, vernum, suff, rev

__all__ = [PortagePackage, PortageSource]
