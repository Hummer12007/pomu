"""
A module to (non)interactively query the user for impure values
"""
from pomu.util.result import Result

def query(name, prompt=None, default=None):
    """
    Queries the impure world for name
    Parameters:
        name - the name
        prompt - prompt text
        default - default value used for errors, forced non-interactive etc.
    TODO: non-interactive
    """
    if not prompt:
        prompt = 'Please enter ' + name
    if default: prompt += ' ({})'.format(default)
    prompt += ' > '
    res = None
    try:
        res = input(prompt)
    except EOFError: pass
    if not res:
        res = default
    if not res:
        return Result.Err('No {} or default provided'.format(name))
    return Result.Ok()
