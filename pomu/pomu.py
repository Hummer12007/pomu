from shutil import rmtree

import click
from git import Repo
import portage
from os import path, makedirs

#TODO: global --repo option, (env var?)

class GlobalVars():
    """Global state"""
    def __init__(self):
        self.no_portage = False
        self.repo_path = None

pass_globals = click.make_pass_decorator(GlobalVars, ensure=True)

@click.group()
@click.option('--no-portage', is_flag=True,
        help='Do not setup the portage repo')
@click.option('--repo-path',
        help='Path to the repo directory (used with --no-portage)')
@pass_globals
def main(globalvars, no_portage, repo_path):
    """A utility to manage portage overlays"""
    globalvars.no_portage = no_portage
    globalvars.repo_path = repo_path

@main.command()
@click.option('--list-repos', is_flag=True,
        help='Lists available repositories')
@click.option('--create', is_flag=True,
        help='Create the repository, instead of using an existing one')
@click.option('--repo-dir', envvar='POMU_REPO_DIR', default='/var/lib/pomu',
        help='Path for creating new repos')
@click.argument('repo', required=False)
@pass_globals
def init(globalvars, list_repos, create, repo_dir, repo):
    """Initialise pomu for a repository"""
    rsets = portage.db[portage.root]['vartree'].settings.repositories
    if list_repos:
        print('Available repos:')
        for prepo in rsets.prepos_order:
            print('\t', prepo, rsets.prepos[prepo].location)
        return
    if globalvars.no_portage:
        init_plain_repo(create, globalvars.repo_path)
    else:
        init_portage_repo(create, repo, repo_dir)

def init_plain_repo(create, repo_path):
    """Initialize a plain repository"""
    if not repo_path:
        print('Error: repository path required')
        return
    if create:
        if path.isdir(repo_path):
            print('Error: this repository already exists')
            return
        try:
            makedirs(repo_path)
        except PermissionError:
            print('Error: you do not have enough permissions to create the git repository')
            return
        Repo.init(repo_path)
        if not init_pomu(repo_path):
            rmtree(repo_path)
    else:
        if not path.isdir(repo_path):
            print('Error: directory not found')
            return
        init_pomu(repo_path)

def init_portage_repo(create, repo, repo_dir):
    """Initialize a portage repository"""
    if not repo:
        print('Error: repository name required')
        return
    rsets = portage.db[portage.root]['vartree'].settings.repositories
    if create:
        if repo in rsets.prepos_order:
            print('Error: a repository with such name already exists!')
            return
        repo_path = path.join(repo_dir, repo)
        try:
            makedirs(repo_path)
        except PermissionError:
            print('Error: you do not have enough permissions to create the git repository')
            return
        try:
            with open(path.join(portage.root, '/etc/portage/repos.conf', 'pomu.conf'), 'a') as f:
                f.write('[' + repo + ']' + '\n')
                f.write('location = ' + repo_path + '\n')
        except PermissionError:
            print('Error: you do not have enough permissions to setup a portage repo')
            rmtree(repo_path)
            return
        Repo.init(repo_path)
        if not init_pomu(repo_path, repo):
            rmtree(repo_path)
    else:
        if repo not in rsets.prepos_order:
            print('Error: repository not found')
            return
        init_pomu(rsets.prepos[repo], repo)

def init_pomu(repo_path, name=' '):
    """Initialise pomu for a repository"""
    pomu_path = path.join(repo_path, 'metadata', 'pomu')
    if not path.isdir(path.join(repo_path, '.git')):
        print('Error: target repository should be a git repo')
        return False
    if path.isdir(pomu_path):
        print('Repository', name, 'already initialized')
        return True
    r = Repo(repo_path)
    try:
        makedirs(pomu_path)
        open(path.join(pomu_path, '.sentinel'), 'w').close()
    except PermissionError:
        print('Error: you do not have enough permissions to modify the repo')
        return False
    r.index.add(pomu_path)
    r.index.commit('Initialized pomu')
    print('Initialized repository', name, 'successfully')
    return True

@main.command()
@pass_globals
def status(globalvars):
    """Display pomu status"""
    if globalvars.no_portage:
        if not globalvars.repo_path:
            print('Error: repo-path required')
            return
        if path.isdir(path.join(globalvars.repo_path, 'metadata', 'pomu')):
            print('pomu is initialized at', globalvars.repo_path)
        print('pomu is not initialized')
    else:
        rsets = portage.db[portage.root]['vartree'].settings.repositories
        for repo in rsets.prepos_order:
            if path.isdir(path.join(rsets.prepos[repo].location, 'metadata', 'pomu')):
                print('pomu is initialized for repository', repo, 'at', rsets.prepos[repo].location)
                return
        print('pomu is not initialized')
