"""
A base package source module.
A package source module shall provide two classes: a class representing
a package (implementation details of the source, package-specific metadata,
fetching logic etc.), and the source per se: it is responsible for parsing
package specifications and fetching the specified package, as well as
instantiating specific packages from the metadata directory.
"""

from pomu.source import dispatcher

class PackageBase():
    """
    This is a base class for storing package-specific metadata.
    It shall be subclassed explicitely.
    The class is responsible for fetching the package, and reading/writing
    the package-specific metadata.
    """

    """The implementation shall provide a name for the package type"""
    __name__ = None

    def fetch(self):
        """
        A method which is responsible for fetching the package: it should return a Package object (specifying set of files with sufficient metadata), and specify this package object as the backend for the Package object (to store source-specific metadata).
        """
        raise NotImplementedError()

    @staticmethod
    def from_data_dir(pkgdir):
        """
        This method is responsible for instantiating source-specific metadata
        from the metadata directory.
        It shall return an instance of this class, and take a path to the meta
        directory.
        """
        raise NotImplementedError()

    def write_meta(self, pkgdir):
        """
        This method shall write source-specific metadata to the provided
        metadata directory.
        """
        raise NotImplementedError()

    def __str__(self):
        """
        The implementation shall provide a method to pretty-print
        package-specific metadata (displayed in show command).
        Example:
        return '{}/{}-{} (from {})'.format(self.category, self.name, self.version, self.path)
        """
        raise NotImplementedError()

@dispatcher.source
class BaseSource:
    """
    This is the base package source class.
    It should be decorated with @dispatcher.source.
    The implementation shall provide methods to parse the package specification,
    which would be called by the dispatcher (see manager.py for details).
    Parser methods shall be decorated with @dispatcher.handler(priority=...)
    decorator (default is 5).
    It shall provide a method to instantiate a package of this type from the
    metadata directory.
    """
    @dispatcher.handler()
    def parse_full(uri):
        """
        This method shall parse a full package specification (which starts with
        the backend name, followed by a colon).
        It shall return a package, wrapped in Result.
        """
        raise NotImplementedError()

    @classmethod
    def from_meta_dir(cls, metadir):
        """
        This method is responsible for instantiating package-specific metadata
        from the metadata directory.
        Example:
        return PackageBase.from_data_dir(metadir)
        """
        raise NotImplementedError()
