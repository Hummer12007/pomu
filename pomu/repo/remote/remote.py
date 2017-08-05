"""A template class for remote repos"""


class RemoteRepo():
    """A class responsible for remotes"""
    def __init__(self, url):
        self.uri = uri
        raise NotImplementedError()

    def fetch_package(self, name, category=None, version=None):
        """Fetches a package, determined by the parametres"""
        raise NotImplementedError()

    def list_cpvs(self):
        """Gets a list of all pebuilds in the repo"""
        raise NotImplementedError()

    def fetch_tree(self):
        """Returns repos hierarchy"""
        raise NotImplementedError()

    def fetch_subtree(self, key):
        """Lists a subtree"""
        raise NotImplementedError()

    def fetch_file(self, key):
        """Fetches a file from the repo"""
        raise NotImplementedError()
