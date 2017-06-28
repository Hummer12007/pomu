"""
A set of utility function to manipulate package descriptions
"""

import re

from pomu.util.portage import suffixes
from pomu.util.str import pivot

def ver_str(vernum, suff, rev):
    """Gets the string representation of the version (specified by number, suffix and rev)"""
    return vernum + (suff if suff else '') + (rev if rev else '')

def cpv_split(pkg):
    """
    Extracts category, name, version number, suffix, revision from a package descriptor
    e.g. dev-libs/openssl-0.9.8z_p8-r100 -> dev-libs, openssl, 0.9.8z, p8, r100
    """
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