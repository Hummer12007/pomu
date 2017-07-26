"""
"""

from os import path
from time import time

from git.repo import Repo

from pomu.util.pkg import cpv_split

def process_changes(_repo):
    # we only tackle repository changes so far
    repo = Repo(_repo.root)
    chans = repo.head.commit.diff(None, create_patch=True)
    new_files = repo.untracked_files
    all_pkgs = _repo.get_packages()
    res = {x: [] for x in all_pkgs}

    ## Process user-made changes to package files
    for f in new_files: # process untracked files
        pkpref = path.dirname(f).split('/')[0:1].join('/')
        if pkpref in res:
            res[pkpref].append(new_file_patch(f))
    for diff in chans: # changes in tracked files
        pkpref = path.dirname(diff.a_path).split('/')[0:1].join('/')
        if pkpref in res:
            res[pkpref].append(diff_header(diff.a_path, diff.b_path).join('\n') +
                    diff.diff.decode('utf-8'))
    res = {x: res[x] for x in res if res[x]}
    for _pkg, diffs in res.items(): # add each change as its own patch
        cat, name, *_ = cpv_split(_pkg)
        patch_contents = diffs.join('\n')
        pkg = _repo.get_package(cat, name)
        patch_name = '{}-user_changes.patch'.format(int(time.time()))
        pkg.add_patch(patch_contents, patch_name)
        repo.index.add([x.a_path for x in diffs])
        repo.index.add([path.join('metadata', cat, name, patch_name)])
        repo.index.commit('{}/{}: imported user changes'.format(cat, name))

    ## Process patch order changes
    res = {x: [] for x in all_pkgs}
    applied = {x: [] for x in all_pkgs}
    for diff in chans:
        if not len(diff.a_path.split('/')) == 4:
            continue
        _, cat, name, __ = diff.a_path.split('/')
        if _ != 'metadata' or __ != 'PATCH_ORDER':
            continue
        if '/'.join([cat, name]) not in res:
            continue
        orig = repo.odb.stream(diff.a_blob.binsha).read().decode('utf-8')
        pkg = _repo.get_package(cat, name)
        orig_lines = [path.join(pkg.pkgdir, x.strip()) for x in orig.split('\n') if x.strip() != '']
        pkg.patches = orig_lines
        pkg.apply_patches(revert=True)
        pkg = _repo.get_package(cat, name)
        pkg.patches = pkg.patch_list
        applied['{}/{}'.format(cat, name)].extend(pkg.patches)
        pkg.apply_patches()
        repo.index.add([diff.a_path, pkg.root])
        repo.index.commit('{}/{}: modified patch order'.format(cat, name))


    ## Process new patch files
    res = {x: [] for x in all_pkgs}
    for f in new_files:
        if not f.startswith('metadata/'):
            continue
        pkpref = path.dirname(f).split('/')[1:2].join('/')
        if f.split('/')[-1] in applied[pkpref]: #skip, we've added the patch in the previous step
            continue
        if pkpref in res:
            res[pkpref].append(f)
    for _pkg, diffs in res.items(): # apply each newly added patch
        pkg = _repo.get_package(cat, name)
        cat, name, *_ = cpv_split(_pkg)
        for d in diffs:
            pkg.patch(d)
        repo.index.add(diffs)
        repo.index.add[path.join(cat, name)]
        repo.index.commit('{}/{}: applied patches'.format(cat, name))

def new_file_patch(repo, newf):
    with open(path.join(repo.root, newf), 'r') as f:
        lines = ['+' + x.strip('\n') for x in f.readlines()]
    head = diff_header('/dev/null', newf, len(lines))
    return (head + lines).join('\n') + '\n'

def diff_header(a_path, b_path, lines=None):
    header = ['--- ' + a_path, '+++ ' + 'b/' + b_path]
    if lines:
        header.append('@@ -0,0 +1,' + lines + ' @@')
    return header
