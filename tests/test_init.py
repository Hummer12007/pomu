from os import makedirs
from shutil import rmtree
import unittest

from pomu.repo.init import init_plain_repo, init_pomu
from pomu.repo.repo import pomu_status
from pomu.util.result import Result

REPO_PATH = 'test_repo'

class RepoInitialization(unittest.TestCase):

    def setUp(self):
        self.REPO_PATH = REPO_PATH

    def tearDown(self):
        rmtree(self.REPO_PATH) 

    def testPlainInitializationAndStatus(self):
        init_plain_repo(True, self.REPO_PATH).expect()
        self.assertEqual(pomu_status(self.REPO_PATH), True)

    def testNonGitInitialization(self):
        makedirs(self.REPO_PATH)
        self.assertEqual(init_pomu(self.REPO_PATH).err(), 'target repository should be a git repo')
