"""
A module to (non)interactively query the user for impure values
"""
from pomu.util.result import Result

class _query:
    def __init__(self):
        self.map = {}
        self.interactive = True

    def __call__(self, name, prompt=None, default=None):
        """
        Queries the impure world for name
        Parameters:
            name - the name
            prompt - prompt text
            default - default value used for errors, forced non-interactive etc.
        TODO: non-interactive
        """
        if name in self.map:
            return Result.Ok(self.map[name])
        if not prompt:
            prompt = 'Please enter ' + name
        if default: prompt += ' ({})'.format(default)
        prompt += ' > '
        res = None
        if self.interactive:
            try:
                res = input(prompt)
            except EOFError: pass
        if not res:
            res = default
        if not res:
            return Result.Err('No {} or default provided'.format(name))
        return Result.Ok(res)

    def set(self, name, val):
        old = None
        if name in self.map:
            old = self.map[name]
        if val is None:
            self.unset(name)
        self.map[name] = val
        return old

    def unset(self, name):
        if name in self.map:
            del self.map[name]

query = _query()

class QueryContext:
    def __init__(self, **kwargs):
        self.map = kwargs

    def __enter__(self):
        self.map_old = {x: query.set(x, self.map[x]) for x in self.map}

    def __exit__(self, ex_type, ex_val, tb):
        for x, y in self.map_old.items():
            query.set(x, y)
