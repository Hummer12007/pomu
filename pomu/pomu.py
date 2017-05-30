import click
import portage
from git import Repo
from portage.os import path, makedirs

#TODO: global --repo option, (env var?)

@click.group()
def main():
    """A utility to manage portage overlays"""
    pass

@main.command()
@click.option('--list-repos', is_flag=True,
        help='Lists available repositories')
@click.option('--create', is_flag=True,
        help='Create the repository, instead of using an existing one')
@click.argument('repo', required=False)
@click.argument('repo-dir', envvar='POMU_REPO_DIR', required=False, default='/var/lib/pomu')
def init(list_repos, create, repo, repo_dir):
    """Initialise pomu for a repository"""
    rs = portage.db[portage.root]['vartree'].settings.repositories
    if list_repos:
        print('Available repos:')
        for repo in rs.prepos_order:
            print('\t', repo, rs.prepos[repo].location)
        return
    if not repo:
        print('Error: repository name required')
        return
    if create:
        if repo in rs.prepos_order:
            print('Error: a repository with such name already exists!')
            return
        repo_path = path.join(repo_dir, repo)
        pomu_path = path.join(repo_path, 'metadata', 'pomu')
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
            # TODO: cleanup the dir
            return
        r = Repo.init(repo_path)
        makedirs(pomu_path)
        open(path.join(pomu_path, '.sentinel'), 'w').close()
        r.index.add(pomu_path)
        r.index.commit('Initialized pomu')
        print('Initialized repository', repo, 'successfully')
    else:
        if repo not in rs.prepos_order:
            print('Error: repository not found')
            return
        repo_path = rs.prepos[repo]
        pomu_path = path.join(repo_path, 'metadata', 'pomu')
        if not path.isdir(path.join(repo_path, '.git')):
            print('Error: target repository should be a git repo')
            return
        if path.isdir(pomu_path):
            print('Repository', repo, 'already initialized')
            return 
        r = Repo(repo_path)
        try:
            makedirs(pomu_path)
            open(path.join(pomu_path, '.sentinel'), 'w').close()
        except PermissionError:
            print('Error: you do not have enough permissions to modify the repo')
            return
        r.index.add(pomu_path)
        r.index.commit('Initialized pomu')
        print('Initialized repository', repo, 'successfully')

@main.command()
def status():
    """Display pomu status"""
    rs = portage.db[portage.root]['vartree'].settings.repositories
    for repo in rs.prepos_order:
        if path.isdir(path.join(rs.prepos[repo].location, 'metadata', 'pomu')):
            print('pomu is initialized for repository', repo, 'at', rs.prepos[repo].location)
            return
    print('pomu is not initialized')
