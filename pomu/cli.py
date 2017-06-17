"""pomu command line interface"""
import click

from pomu.repo.init import init_plain_repo, init_portage_repo
from pomu.repo.repo import portage_repo_path, portage_repos, pomu_active_repo
from pomu.source import dispatcher
from pomu.util.result import ResultException

#TODO: global --repo option, (env var?)

class GlobalVars():
    """Global state"""
    def __init__(self):
        self.no_portage = False
        self.repo_path = None

g_params = GlobalVars()

class needs_repo():
    def __init__(self, func):
        self.func = func
        self.__name__ = func.__name__

    def __call__(self, *args):
        pomu_active_repo(g_params.no_portage, g_params.repo_path)
        self.func(*args)

pass_globals = click.make_pass_decorator(GlobalVars, ensure=True)

@click.group()
@click.option('--no-portage', is_flag=True,
        help='Do not setup the portage repo')
@click.option('--repo-path',
        help='Path to the repo directory (used with --no-portage)')
def main(no_portage, repo_path):
    """A utility to manage portage overlays"""
    g_params.no_portage = no_portage
    g_params.repo_path = repo_path

@main.command()
@click.option('--list-repos', is_flag=True,
        help='Lists available repositories')
@click.option('--create', is_flag=True,
        help='Create the repository, instead of using an existing one')
@click.option('--repo-dir', envvar='POMU_REPO_DIR', default='/var/lib/pomu',
        help='Path for creating new repos')
@click.argument('repo', required=False)
def init(g_params, list_repos, create, repo_dir, repo):
    """Initialise pomu for a repository"""
    if list_repos:
        print('Available repos:')
        for prepo in portage_repos():
            print('\t', prepo, portage_repo_path(prepo))
        return
    if g_params.no_portage:
        print(init_plain_repo(create, g_params.repo_path).expect())
    else:
        print(init_portage_repo(create, repo, repo_dir).expect())

@main.command()
@needs_repo
def status():
    """Display pomu status"""
    repo = pomu_active_repo()
    if repo.name:
        print('pomu is initialized for reporitory', repo.name, 'at', repo.root)
    else:
        print('pomu is initialized at', repo.root)

@main.command()
@click.argument('package', required=True)
@needs_repo
def install(package):
    res = dispatcher.install_package(package).expect()
    print(res)

@main.command()
@click.option('--uri', is_flag=True,
        help='Specify the package to remove by uri, instead of its name')
@click.argument('package', required=True)
@needs_repo
def uninstall(uri, package):
    if uri:
        res = dispatcher.uninstall_package(package).expect()
        print(res)
    else:
        repo = pomu_active_repo()
        res = repo.remove_package(package).expect()
        return res

@main.command()
@click.argument('package', required=True)
@needs_repo
def fetch(package):
    pkg = dispatcher.get_package(package).expect()
    print('Fetched package', pkg.name, 'at', pkg.root)

def main_():
    try:
        main.main(standalone_mode=False)
    except ResultException as e:
        print(str(e))

if __name__ == '__main__':
    main_()
