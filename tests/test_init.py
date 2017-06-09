import importlib
import os
from shutil import rmtree
import unittest

import portage

from pomu.repo.init import init_plain_repo, init_pomu, init_portage_repo
from pomu.repo.repo import pomu_status, portage_repos, pomu_active_repo

REPO_DIR = 'test_repo'
REPO_PATH = os.path.join(os.getcwd(), REPO_DIR)

class PlainRepoInitialization(unittest.TestCase):

    def setUp(self):
        self.REPO_DIR = REPO_DIR

    def tearDown(self):
        rmtree(self.REPO_DIR)

    def testPlainInitializationAndStatus(self):
        init_plain_repo(True, self.REPO_DIR).expect()
        self.assertEqual(pomu_status(self.REPO_DIR), True)

    def testNonGitInitialization(self):
        os.makedirs(self.REPO_DIR)
        self.assertEqual(init_pomu(self.REPO_DIR).err(), 'target repository should be a git repo')

class PortageRepoInitialization(unittest.TestCase):

    def setUp(self):
        os.environ['EROOT'] = REPO_PATH
        os.environ['ROOT'] = REPO_PATH
        os.environ['PORTAGE_CONFIGROOT'] = REPO_PATH
        rcp = os.path.join(REPO_PATH, 'etc/portage/repos.conf')
        os.makedirs(rcp)
        with open(os.path.join(rcp, 'gentoo.conf'), 'w') as f:
            f.write('[DEFAULT]\nmain-repo = gentoo\n[gentoo]\nlocation=/usr/portage\n')
        importlib.reload(portage)
        self.REPO_DIR = REPO_DIR

    def tearDown(self):
        rmtree(REPO_PATH)

    def testRepoList(self):
        self.assertEqual(list(portage_repos()), ['gentoo'])

    def testPortageCreate(self):
        self.assertTrue(init_portage_repo(True, REPO_DIR, REPO_PATH).is_ok())
        importlib.reload(portage)
        self.assertEqual(pomu_active_repo(), REPO_DIR)
