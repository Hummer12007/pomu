def pivot(string, idx, keep_pivot=True):
    if keep_pivot:
        return (string[:idx], string[idx:])
    else:
        return (string[:idx], string[idx+1:])
