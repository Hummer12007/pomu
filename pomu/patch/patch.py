"""
"""

from os import path, walk, makedirs
from shutil import copy2
from time import time

import subprocess

from git.repo import Repo
from patch import PatchSet

from pomu.repo.repo import Repository
from pomu.util.fs import strip_prefix
from pomu.util.misc import list_add
from pomu.util.pkg import cpv_split
from pomu.util.result import Result

def process_changes(_repo):
    # we only tackle repository changes so far
    repo = Repo(_repo.root)
    chans = repo.head.commit.diff(None, create_patch=True)
    new_files = repo.untracked_files
    all_pkgs = _repo.get_packages
    res = {x: [] for x in all_pkgs}
    pkgs = ls
    for f in new_files: # process untracked files
        pkpref = path.dirname(f).split('/')[0:1].join('/')
        if pkpref in res:
            res[pkpref].append(new_file_patch(f))
    for diff in chans: # changes in tracked files
        pkpref = path.dirname(diff.a_path).split('/')[0:1].join('/')
        if pkpref in res:
            res[pkpref].append(header(diff.a_path, diff.b_path).join('\n') +
                    diff.diff.decode('utf-8'))
    res = {x: res[x] for x in res if res[x]}
    for _pkg, diffs in res.items(): # add each change as its own patch
        cat, name, *_ = cpv_split(_pkg)
        patch_contents = diffs.join('\n')
        pkg = _repo.get_package(cat, name)
        patch_name = '{}-user_changes.patch'.format(int(time.time()))
        pkg.add_patch(patch_contents, patch_name)
        repo.index.add([x.a_path for x in diffs])
        repo.index.add([path.join(_repo.root, 'metadata', cat, name, patch_name)])
        repo.index.commit('{}/{}: imported user changes'.format(cat, name))

def new_file_patch(repo, newf):
    with open(path.join(repo.root, newf), 'r') as f:
        lines = ['+' + x.strip('\n') for x in f.readlines()]
    head = header('/dev/null', newf, len(lines))
    return (head + lines).join('\n') + '\n'

def diff_header(a_path, b_path, lines=None):
    header = ['--- ' + a_path, '+++ ' + 'b/' + b_path]
    if lines:
        header.append('@@ -0,0 +1,' + lines + ' @@')
    return header
