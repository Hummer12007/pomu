"""Subroutines with repositories"""
from os import path

import portage

rsets = portage.db[portage.root]['vartree'].settings.repositories

def portage_repos():
    for repo in rsets.prepos_order:
        yield repo

def portage_repo_path(repo):
    """Get the path of a given portage repository"""
    if repo in rsets.prepos_order:
        return rsets.prepos[repo].location
    return None

def pomu_status(repo_path):
    """Check if pomu is enabled for a repository at a given path"""
    return path.isdir(path.join(repo_path, 'metadata', 'pomu'))
