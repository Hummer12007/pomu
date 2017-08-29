"""
Utilities for remotes
"""

from portage.versions import best

from pomu.util.pkg import ver_str, cpv_split
from pomu.util.portage import misc_dirs

from pomu.util.result import Result

def filelist_to_cpvs(tree):
    """Converts a list of files to list of cpvs"""
    res = []
    for opath in tree:
        comps = opath.split('/')
        if (opath.endswith('/') or
            any(opath.startswith('/' + x + '/') for x in misc_dirs) or
            len(comps) != 3 or
            not comps[2].endswith('.ebuild')):
            continue
        category, name, ebuild = comps[0], comps[1], comps[2][:-7]
        c, n, v, s, r = cpv_split(ebuild)
        if category or n != name:
            continue
        ver = ver_str(v, s, r)
        res.append((category, name, ver))
    return res

def get_full_cpv(cpvs, name, category=None, version=None):
    cpvl = cpvs.filter(lambda x: x[1] == name and (not category or x[0] == category))
    if not cpvl: return Result.Err()
    if version:
        cpvl = cpvl.filter(lambda x: x[2] == version)[:1]
    b = best('{}/{}-{}'.format(c, n, v) for c, n, v in cpvl)
    if b:
        cat, name, v, s, r = cpv_split(b)
        ver = ver_str(v, s, r)
        return Result.Ok((cat, name, ver))
    return Result.Err()
