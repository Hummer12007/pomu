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

from pomu.repo.repo import pomu_active_repo
from pomu.util.result import Result

class PackageDispatcher():
    def __init__(self):
        self.handlers = []

    def source(self, cls):
        for m, obj in inspect.getmembers(cls):
            if isinstance(obj, self.handler._handler):
                self.register_package_handler(cls, obj.handler, obj.priority)
        return cls

    class handler():
        class _handler():
            def __init__(self, handler):
                self.handler = handler
            def __call__(self, *args):
                return self.handler(*args)

        def __init__(self, priority=1000, *args, **kwargs):
            self.priority = priority

        def __call__(self, func, *args, **kwargs):
            x = self._handler(func)
            x.priority = self.priority
            return x

    def register_package_handler(self, source, handler, priority):
        i = 0
        for i in range(len(self.handlers)):
            if self.handlers[0] > priority:
                break
        self.handlers.insert(i, (priority, source, handler))

    def get_package_source(self, uri):
        for priority, source, handler in self.handlers:
            if handler(uri).is_ok():
                return source
        return None

    def get_package(self, uri):
        for priority, source, handler in self.handlers:
            res = handler(uri)
            if res.is_ok():
                return Result.Ok(source.fetch_package(res.ok()))
        return Result.Err('No handler found for package ' + uri)

    def install_package(self, uri):
        pkg = self.get_package(uri).unwrap()
        return pomu_active_repo().merge(pkg)

    def uninstall_package(self, uri):
        pkg = self.get_package(uri).unwrap()
        return pomu_active_repo().unmerge(pkg)
