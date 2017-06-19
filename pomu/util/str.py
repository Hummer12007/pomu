"""String processing utilities"""
def pivot(string, idx, keep_pivot=True):
    """
    A function to split a string in two, pivoting at string[idx].
    If keep_pivot is set, the pivot character is included in the second string.
    Alternatively, it is omitted.
    """
    if keep_pivot:
        return (string[:idx], string[idx:])
    else:
        return (string[:idx], string[idx+1:])
