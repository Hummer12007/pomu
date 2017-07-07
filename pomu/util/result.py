"""Result type module"""

class ResultException(Exception):
    pass

class Result():
    """Result = Err E | Ok V"""

    def __init__(self, is_val):
        self._is_val = is_val

    @classmethod
    def Ok(cls, val=None):
        res = cls(True)
        res._val = val
        return res

    @classmethod
    def Err(cls, val=None):
        res = cls(False)
        res._val = val
        return res

    def is_ok(self):
        return self._is_val

    def is_err(self):
        return not self._is_val

    def ok(self):
        return self._val if self._is_val else None

    def err(self):
        return self._val if not self._is_val else None

    def map(self, f):
        return Result.Ok(f(self.ok())) if self._is_val else Result.Err(self.err())

    def map_err(self, f):
        return Result.Err(f(self.err())) if not self._is_val else Result.Ok(self.ok())

    def unwrap(self):
        return self.expect()

    def expect(self, msg='Error'):
        if self._is_val:
            return self._val
        raise ResultException(msg + ': ' + self._val)

    def unwrap_err(self):
        return self.expect_err()

    def expect_err(self, msg='Error'):
        if not self._is_val:
            return self._val
        raise ResultException(msg + ': ' + self._val)

    def and_(self, rhs):
        if not self.is_ok():
            return Result.Err(self.err())
        return rhs

    def and_then(self, f):
        return self.map(f)

    def or_(self, rhs):
        if self.is_ok():
            return Result.Ok(self.ok())
        return rhs

    def __iter__(self):
        if self._is_val:
            yield self._val
