"""Subroutines with repositories"""
from os import path

import portage

def portage_repos():
    """Yield the repositories configured for portage"""
    rsets = portage.db[portage.root]['vartree'].settings.repositories

    for repo in rsets.prepos_order:
        yield repo

def portage_repo_path(repo):
    """Get the path of a given portage repository"""
    rsets = portage.db[portage.root]['vartree'].settings.repositories

    if repo in rsets.prepos:
        return rsets.prepos[repo].location
    return None

def pomu_status(repo_path):
    """Check if pomu is enabled for a repository at a given path"""
    return path.isdir(path.join(repo_path, 'metadata', 'pomu'))

def pomu_active_repo():
    """Returns a portage repo, for which pomu is enabled"""
    for repo in portage_repos():
        if pomu_status(portage_repo_path(repo)):
            return repo
    return None
