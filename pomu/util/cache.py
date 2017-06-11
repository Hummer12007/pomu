"""
Caches the return value of a function -> Result, regardless of input params
"""
class cached():
    def __init__(self, fun):
        self.fun = fun
    def __call__(self, *args):
        if not hasattr(self, 'retval'):
            self.retval = self.fun(*args).unwrap()
        return self.retval
