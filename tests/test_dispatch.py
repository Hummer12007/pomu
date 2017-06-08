import unittest
from os import path
from tempfile import mkdtemp

import pomu.source
from pomu.package import Package
from pomu.repo.repo import pomu_status, portage_repos, portage_active_repo
from pomu.util.result import Result

@dispatcher.source
class DummySource():
    def __init__(self, _path):
        self.path = _path

    @dispatcher.handler
    def parse(self, uri):
        return Result.Ok(uri)

    def fetch_package(self, uri):
        return Package('test', self.path)

class InstallTests(unittests.TestCase):

    def setUp(self):
        source_path = mkdtemp()
        with path.join(source_path, 'test.ebuild') as f:
            f.write('# Copytight 1999-2017\nAll Rights Reserved\nEAPI="0"\n')
        self.source = DummySource(source_path)
