"""
String utils
"""

def strip_prefix(string, prefix):
    """Returns a string, stripped from its prefix"""
    if string.startswith(prefix):
        return string[len(prefix):]
    else
        return string
