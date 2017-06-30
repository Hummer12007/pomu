import shutil
import unittest

from os import path
from tempfile import mkdtemp

from pomu.package import Package
from pomu.repo.init import init_plain_repo
from pomu.repo.repo import Repository, pomu_active_repo
from pomu.source import dispatcher
from pomu.util.result import Result

@dispatcher.source
class DummySource():
    @dispatcher.handler(priority=3)
    def parse(uri):
        if uri.startswith('/'):
            return Result.Ok(uri[1:])
        return Result.Err()

    @classmethod
    def fetch_package(cls, uri):
        return Package(cls, 'test', cls.path)

class DispatcherTests(unittest.TestCase):
    def setUp(self):
        pomu_active_repo._drop()
        self.source_path = mkdtemp()
        with open(path.join(self.source_path, 'test.ebuild'), 'w+') as f:
            f.write('# Copytight 1999-2017\nAll Rights Reserved\nEAPI="0"\n')
        DummySource.path = self.source_path

    def testDispatch(self):
        self.assertEqual(dispatcher.get_package_source('/test').unwrap(), DummySource)
        self.assertTrue(dispatcher.get_package_source('test').is_err())
        self.assertTrue(dispatcher.get_package('sys-apps/portage').is_ok())

    def testFetch(self):
        pkg = dispatcher.get_package('/test').unwrap()
        self.assertEqual(pkg.files, [('', 'test.ebuild')])

    def tearDown(self):
        shutil.rmtree(self.source_path)

"""
class InstallTests(unittest.TestCase):
    def setUp(self):
        pomu_active_repo._drop()
        self.source_path = mkdtemp()
        with open(path.join(self.source_path, 'test.ebuild'), 'w+') as f:
            f.write('# Copytight 1999-2017\nAll Rights Reserved\nEAPI="0"\n')
        DummySource.path = self.source_path

        self.repo_dir = mkdtemp()
        shutil.rmtree(self.repo_dir)
        init_plain_repo(True, self.repo_dir).expect()
        self.repo = Repository(self.repo_dir)

    def tearDown(self):
        shutil.rmtree(self.repo_dir)

    def testPkgCreate(self):
        pkg = Package('test', self.source_path, files=['test.ebuild'])
        self.assertEqual(pkg.files, [('', 'test.ebuild')])

    def testPkgMerge(self):
        pkg = Package('test', self.source_path)
        self.repo.merge(pkg).expect()

    def testPortagePkg(self):
        pkg = dispatcher.get_package('sys-apps/portage').expect()
        self.repo.merge(pkg).expect()

    def testPkgUnmerge(self):
        pkg = Package('test', self.source_path)
        self.repo.merge(pkg).expect()
        with self.subTest(i=0):
            self.repo.unmerge(pkg).expect()
        with self.subTest(i=1):
            self.repo.remove_package('test').expect()
        with self.subTest(i=2):
            self.repo.remove_package('tset').expect_err()
"""
