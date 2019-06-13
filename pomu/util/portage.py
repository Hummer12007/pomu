"""
A set of utility functions to query portage repos
"""

import os

from os import path

from portage.versions import best

from pomu.repo.repo import portage_repos, portage_repo_path
from pomu.util.pkg import cpv_split, ver_str

misc_dirs = ['profiles', 'licenses', 'eclass', 'metadata', 'distfiles', 'packages', 'scripts', '.git']

def best_ver(repo, category, name, ver=None):
    """Gets the best (newest) version of a package in the repo"""
    if ver:
        return ver if path.exists(path.join(portage_repo_path(repo),
            category, name, '{}-{}.ebuild'.format(name, ver))) else None
    ebuilds = [category + '/' + name + x[len(name):-7] for x in
            os.listdir(path.join(portage_repo_path(repo), category, name))
            if x.endswith('.ebuild')]
    if not ebuilds:
        return None
    cat, name, ver = cpv_split(best(ebuilds))
    return ver

def repo_pkgs(repo, category, name, ver=None, slot=None):
    """List of package occurences in the repo"""
    if not repo:
        res = []
        for r in portage_repos():
            res.extend(repo_pkgs(r, category, name, ver, slot))
        return res
    if category:
        if path.exists(path.join(portage_repo_path(repo), category, name)):
            res = best_ver(repo, category, name, ver)
            return [(repo, category, name, res)] if res else []
        return []
    rpath = portage_repo_path(repo)
    dirs = set(os.listdir(rpath)) - set(misc_dirs)
    res = []
    for d in dirs:
        if path.isdir(path.join(rpath, d, name)):
            res.append((repo, d, name, best_ver(repo, d, name, ver)))
    return res

