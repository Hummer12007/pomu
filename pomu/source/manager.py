"""
Package source manager is responsible for selecting the correct source
for a requested package, by a provided string.

Package sources can provide several handlers with different priorities.
A handler is a String -> Result function, which tries to parse the passed
value and return Ok(value).

The package would be handled by the handler with the lowest priority, which
was added the first.

Example:
    @dispatcher.source
    class BgoSource():
        @dispatcher.handler(priority=5)
        def parse_int(uri):
            if uri.is_decimal():
                return Result.Ok(int(uri))
            elif uri[0] == '#' and uri[1:].is_decimal():
                return Result.Ok(int(uri[1:]))
            return Result.Err('NaN')

        @dispatcher.handler(priority=1)
        def parse_url(uri):
            if uri.startswith('http://bugs.gentoo.org/'):
            ...
"""
#TODO: efficient sorted insertion
#import bisect
import inspect

from pomu.util.result import Result

class PackageDispatcher():
    def __init__(self):
        self.handlers = []
        self.backends = {}

    def source(self, cls):
        """
        A decorator to mark package source modules
        It would register all the methods of the class marked by @handler
        with the dispatcher.
        """
        try:
            from pomu.source.base import BaseSource
        except ImportError: #circular import
            return cls
        if cls == BaseSource:
            return cls
        self.backends[cls.__cname__] = cls
        for m, obj in inspect.getmembers(cls):
            if isinstance(obj, self.handler._handler):
                self.register_package_handler(cls, obj.handler, obj.priority)
        return cls

    class handler():
        """
        A decorator to denote package source module handler, which
        should attempt to parse a package descriptor. If it succeeds,
        the result would be passed to the module for further processing.
        """
        class _handler():
            def __init__(self, handler):
                self.handler = handler
            def __call__(self, *args, **kwargs):
                return self.handler(*args, **kwargs)

        def __init__(self, priority=1000, *args, **kwargs):
            self.priority = priority

        def __call__(self, func, *args, **kwargs):
            x = self._handler(func)
            x.priority = self.priority
            return staticmethod(x)

    def register_package_handler(self, source, handler, priority):
        """
        Register a package handler for a specified source.
        Handlers with lower priority get called first.
        """
        i = 0
        for i in range(len(self.handlers)):
            if self.handlers[i][0] > priority:
                break
        self.handlers.insert(i, (priority, source, handler))

    def get_package_source(self, uri):
        """Get a source which accepts the package"""
        for priority, source, handler in self.handlers:
            if handler(uri).is_ok():
                return Result.Ok(source)
        return Result.Err('No handler found for package ' + uri)

    def get_package(self, uri):
        """Fetch a package specified by the descriptor"""
        for priority, source, handler in self.handlers:
            res = handler(uri)
            if res.is_ok():
                return Result.Ok(source.fetch_package(res.ok()))
        return Result.Err('No handler found for package ' + uri)

    def install_package(self, repo, uri):
        """Install a package specified by the descriptor into the repository"""
        pkg = self.get_package(uri).unwrap()
        return repo.merge(pkg)

    def uninstall_package(self, repo, uri):
        """Uninstall a package specified by the descriptor"""
        pkg = self.get_package(uri).unwrap()
        return repo.unmerge(pkg)
