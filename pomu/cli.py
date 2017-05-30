"""pomu command line interface"""
import click

from pomu.repo.init import init_plain_repo, init_portage_repo
from pomu.repo.repo import portage_repo_path, portage_repos, pomu_status
from pomu.util.result import ResultException

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
    if list_repos:
        print('Available repos:')
        for prepo in portage_repos():
            print('\t', prepo, portage_repo_path(prepo))
        return
    try:
        if globalvars.no_portage:
            print(init_plain_repo(create, globalvars.repo_path).expect())
        else:
            print(init_portage_repo(create, repo, repo_dir).expect())
    except ResultException as e:
        print(str(e))

@main.command()
@pass_globals
def status(globalvars):
    """Display pomu status"""
    if globalvars.no_portage:
        if not globalvars.repo_path:
            print('Error: repo-path required')
            return
        if pomu_status(globalvars.repo_path):
            print('pomu is initialized at', globalvars.repo_path)
        print('pomu is not initialized')
    else:
        for repo in portage_repos():
            if pomu_status(portage_repo_path(repo)):
                print('pomu is initialized for repository', repo, 'at', portage_repo_path(repo))
                return
        print('pomu is not initialized')

