"""Miscellaneous utility functions"""

def list_add(dst, src):
    """
    Extends the target list with a scalar, or contents of the given list
    """
    if isinstance(src, list):
        dst.extend(src)
    else:
        dst.append(src)


def pivot(string, idx, keep_pivot=False):
    """
    A function to split a string in two, pivoting at string[idx].
    If keep_pivot is set, the pivot character is included in the second string.
    Alternatively, it is omitted.
    """
    if keep_pivot:
        return (string[:idx], string[idx:])
    else:
        return (string[:idx], string[idx+1:])
