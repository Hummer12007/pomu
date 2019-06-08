"""
A base package source module.
A package source module shall provide two classes: a class representing
a package (implementation details of the source, package-specific metadata,
fetching logic etc.), and the source per se: it is responsible for parsing
package specifications and fetching the specified package, as well as
instantiating specific packages from the metadata directory.
"""

from os import path

from pomu.source import dispatcher
from pomu.util.result import Result

class PackageBase():
    """
    This is a base class for storing package-specific metadata.
    It shall be subclassed explicitely.
    The class is responsible for fetching the package, and reading/writing
    the package-specific metadata.
    """

    """The implementation shall provide a name for the package type"""
    __cname__ = None

    def __init__(self, category, name, version, slot='0'):
        """
        Unified basic metadata storage for all the sources
        """
        self.category = category
        self.name = name
        self.version = version
        self.slot = slot

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
        try:
            lines = [x.strip() for x in open(path.join(pkgdir, 'PACKAGE_BASE_DATA'), 'r')]
        except:
            return Result.Err('Could not read data file')
        if len(lines) < 4:
            return Result.Err('Invalid data provided')
        category, name, version, slot, *_ = lines
        return Result.Ok(PackageBase(category, name, version, slot))

    def write_meta(self, pkgdir):
        """
        This method shall write source-specific metadata to the provided
        metadata directory.
        """
        with open(path.join(pkgdir, 'PACKAGE_BASE_DATA'), 'w') as f:
            f.write(self.category + '\n')
            f.write(self.name + '\n')
            f.write(self.version + '\n')
            f.write(self.slot + '\n')

    def __str__(self):
        """
        The implementation shall provide a method to pretty-print
        package-specific metadata (displayed in show command).
        """
        return '{}/{}:{}-{}'.format(self.category, self.name, '' if self.slot == '0' else ':' + self.slot, self.version)

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
    __cname__ = None

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
