"""Subroutines for repository initialization"""
from shutil import rmtree

from git import Repo
from os import path, makedirs
import portage

from pomu.util.result import Result, ResultException

def init_plain_repo(create, repo_path, name=None): #name might be extraneous
    """Initialize a plain repository"""
    if not repo_path:
        return Result.Err('repository path required')
    if create:
        if path.isdir(repo_path):
            return Result.Err('this repository already exists')
        try:
            makedirs(repo_path)
        except PermissionError:
            return Result.Err('you do not have enough permissions to create the git repository')
        Repo.init(repo_path)
        try:
            return Result.Ok(init_new(repo_path).unwrap())
        except ResultException as e:
            rmtree(repo_path)
            return Result.Err(str(e))
    else:
        if not path.isdir(repo_path):
            return Result.Err('directory not found')
        return init_pomu(repo_path)

def init_portage_repo(create, repo, repo_dir):
    """Initialize a portage repository"""
    if not repo:
        return Result.Err('repository name required')
    rsets = portage.db[portage.root]['vartree'].settings.repositories
    if create:
        if repo in rsets.prepos_order:
            return Result.Err('a repository with such name already exists!')
        repo_path = path.join(repo_dir, repo)
        try:
            makedirs(repo_path)
        except PermissionError:
            return Result.Err('you do not have enough permissions to create the git repository')
        try:
            with open(path.join(portage.root, 'etc/portage/repos.conf', 'pomu.conf'), 'a') as f:
                f.write('[' + repo + ']' + '\n')
                f.write('location = ' + repo_path + '\n')
        except PermissionError:
            rmtree(repo_path)
            return Result.Err('you do not have enough permissions to setup a portage repo')
        Repo.init(repo_path)
        try:
            return Result.Ok(init_new(repo_path, repo).unwrap())
        except ResultException as e:
            rmtree(repo_path)
            return Result.Err(str(e))
    else:
        if repo not in rsets.prepos_order:
            return Result.Err('repository not found')
        return init_pomu(rsets.prepos[repo], repo)

def init_new(repo_path, name=None):
    """Initialize a newly created repository (metadata/layout.conf and pomu)"""
    cnf = path.join(repo_path, 'metadata', 'layout.conf')
    if not path.isfile(cnf):
        try:
            makedirs(path.join(repo_path, 'metadata'))
            with open(cnf, 'w') as f:
                f.write('masters = gentoo\n')
        except PermissionError:
            return Result.Err('you do not have enough permissions to modify the repo')
    return init_pomu(repo_path, name)

def init_pomu(repo_path, name=None):
    """Initialise pomu for a repository"""
    pomu_path = path.join(repo_path, 'metadata', 'pomu')
    if not path.isdir(path.join(repo_path, '.git')):
        return Result.Err('target repository should be a git repo')
    if path.isdir(pomu_path):
        return Result.Ok('Repository ' + name if name else 'at {}'.format(repo_path) + ' already initialized')
    r = Repo(repo_path)
    try:
        makedirs(pomu_path)
        open(path.join(pomu_path, '.sentinel'), 'w').close()
    except PermissionError:
        return Result.Err('you do not have enough permissions to modify the repo')
    r.index.add([path.join('metadata', 'pomu')])
    r.index.commit('Initialized pomu')
    ret = Result.Ok('Initialized repository ' + name + ' successfully')
    return ret
