"""
"""

from os import path
from time import time

from git.repo import Repo

from pomu.util.pkg import cpv_split
from pomu.util.result import Result

def process_changes(_repo, single):
    # we only tackle repository changes so far
    repo = Repo(_repo.root)
    chans = repo.head.commit.diff(None, create_patch=True)
    new_files = repo.untracked_files
    all_pkgs = _repo.get_packages()
    res = {x: [] for x in all_pkgs}
    paths = {x: [] for x in all_pkgs}
    multi = not single
    chanpaks = ([],[],[]) # import, order, apply

    ## Process user-made changes to package files
    for f in new_files: # process untracked files
        pkpref = '/'.join(path.dirname(f).split('/')[0:2])
        if pkpref in res:
            paths[pkpref].append(f)
            res[pkpref].append(new_file_patch(_repo, f))
    for diff in chans: # changes in tracked files
        pkpref = '/'.join(path.dirname(diff.a_path).split('/')[0:2])
        if pkpref in res:
            paths[pkpref].append(diff.a_path)
            res[pkpref].append('\n'.join(diff_header(diff.a_path, diff.b_path)) +
                    diff.diff.decode('utf-8'))
    res = {x: res[x] for x in res if res[x]}
    paths = {x: paths[x] for x in paths if res[x]}
    for _pkg, diffs in res.items(): # add each change as its own patch
        cat, name, _ = cpv_split(_pkg)
        patch_contents = '\n'.join(diffs)
        pkg = _repo.get_package(name, cat).expect()
        patch_name = '{}-user_changes.patch'.format(int(time()))
        had_order = path.exists(path.join(pkg.pkgdir, 'patches', 'PATCH_ORDER'))
        pkg.add_patch(patch_contents, patch_name)
        repo.index.add([p for ps in paths for p in paths[ps]])
        repo.index.add([path.join(pkg.pkgdir, 'patches', patch_name)])
        if not had_order:
            repo.index.add([path.join(pkg.pkgdir, 'PATCH_ORDER')])
        if multi:
            repo.index.commit('{}/{}: imported user changes'.format(cat, name))
        else:
            chanpaks[0].append('{}/{}'.format(cat, name))

    ## Process patch order changes
    res = {x: [] for x in all_pkgs}
    applied = {x: [] for x in all_pkgs}
    for diff in chans:
        if not len(diff.a_path.split('/')) == 4:
            continue
        _, cat, name, __ = diff.a_path.split('/')
        if _ != 'metadata' and __ != 'PATCH_ORDER':
            continue
        if '/'.join([cat, name]) not in res:
            continue
        orig = repo.odb.stream(diff.a_blob.binsha).read().decode('utf-8')
        pkg = _repo.get_package(name, cat)
        orig_lines = [path.join(pkg.pkgdir, x.strip()) for x in orig.split('\n') if x.strip() != '']
        pkg.patches = orig_lines
        pkg.apply_patches(revert=True)
        pkg = _repo.get_package(name, cat)
        pkg.patches = pkg.patch_list
        applied['{}/{}'.format(cat, name)].extend(pkg.patches)
        pkg.apply_patches()
        repo.index.add([diff.a_path, pkg.root])
        if multi:
            repo.index.commit('{}/{}: modified patch order'.format(cat, name))
        else:
            chanpaks[1].append('{}/{}'.format(cat, name))


    ## Process new patch files
    res = {x: [] for x in all_pkgs}
    for f in new_files:
        if not f.startswith('metadata/') or f.split('/')[-1] == 'PATCH_ORDER':
            continue
        pkpref = '/'.join(path.dirname(f).split('/')[2:4])
        if f.split('/')[-1] in applied[pkpref]: #skip, we've added the patch in the previous step
            continue
        if pkpref in res:
            res[pkpref].append(f)
    for _pkg, diffs in res.items(): # apply each newly added patch
        cat, name, _ = cpv_split(_pkg)
        pkg = _repo.get_package(name, cat).expect()
        for d in diffs:
            pkg.patch(d)
        repo.index.add(diffs)
        repo.index.add([path.join(cat, name)])
        if multi:
            repo.index.commit('{}/{}: applied patches'.format(cat, name))
        else:
            chanpaks[2].append('{}/{}'.format(cat, name))

    if not multi:
        msg = 'Synced modifications:\n'
        if chanpaks[0]:
            msg += '\nimported user changes:\n' + '\n'.join(chanpaks[0]) + '\n'
        if chanpaks[1]:
            msg += '\nmodified patch order:\n' + '\n'.join(chanpaks[1]) + '\n'
        if chanpaks[2]:
            msg += '\napplied patches:\n' + '\n'.join(chanpaks[2]) + '\n'

    return Result.Ok()

def new_file_patch(repo, newf):
    with open(path.join(repo.root, newf), 'r') as f:
        lines = ['+' + x.strip('\n') for x in f.readlines()]
    head = diff_header('/dev/null', newf, len(lines))
    return '\n'.join(head + lines) + '\n'

def diff_header(a_path, b_path, lines=None):
    header = ['--- ' + a_path, '+++ ' + 'b/' + b_path]
    if lines:
        header.append('@@ -0,0 +1,' + lines + ' @@')
    return header
