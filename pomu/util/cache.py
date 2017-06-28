"""
Caches the return value of a function -> Result, regardless of input params
"""
class cached():
    """
    A decorator to make the function cache its return value, regardless of input
    """
    def __init__(self, fun):
        self.fun = fun
        self.__name__ = fun.__name__
    def __call__(self, *args):
        if not hasattr(self, 'retval'):
            self.retval = self.fun(*args).unwrap()
        return self.retval
