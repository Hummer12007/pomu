# Pomu

##Prerequisites

pomu requires the following packages to be installed:

- sys-apps/portage	 : Portage repository querying and management
- app-portage/repoman	 : Manifest generation
- dev-python/click	 : CLI implementation
- dev-python/git-python	 : Git repository management and initialization

In addition to the necessary dependencies, pomu requires a git ebuild repository (optionally set up with portage), though it can create a new one as well (with or without setting it up in portage).

## Usage

Usage: pomu [OPTIONS] COMMAND [ARGS]...

  A utility to manage portage overlays

Options:
  --no-portage      Do not setup the portage repo
  --repo-path TEXT  Path to the repo directory (used with --no-portage)
  --help            Show this message and exit.

Commands:
  fetch      Fetch a package into a directory
  init       Initialise pomu for a repository
  install
  show
  status
  uninstall

## Planned functionality

1) create/use a git repository/directory, in a configurable location (default may be /usr/local/portage),
with an option to set it up as a repo in /etc/portage/repos.conf;

2) import ebuilds and related files (FILESDIR, eclasses, dependent ebuilds (if required) etc.) in atomic
commits with meaningful descriptions;

3) import packages from:
* the portage tree
* overlays (either in fs or in remote repositories, including, but not limited to, overlays in the layman
catalog, arbitrary git repos (with proper layout) etc.)
* local/remote text files
* bugzilla tickets (from ebuild/patch attachments, and (optionally) from links in comments (at least (may
be extended) serving text/plain content))
* github pull requests (may be extended to support repos other than gentoo/gentoo)
* (possibly) some sane pastebin services (like github gists, paste.pound-python.org etc.);

4) when importing packages:
* (from overlays) detect dependencies/eclasses unique to the overlay (unavailable in parent overlays/main
tree) and (prompt the user to) import them
* (from overlays/portage) detect user changes and merge remote changes hunk by hunk (in a manner
similar to dispatch-conf)
* allow the user to specify package category/name (when importing from files/pastebins/patches, and new
package version
* generate required files (Manifests etc.)

4) search for packages, interfacing with gpo.zugaina.org;

5) update ebuilds pulled in from portage/overlays, merging upstream and user changes;

6) remove packages from the repository (if possible, by simply reverting the relevant commits, unless some
non-leaf packages/eclasses pulled in by the package are required for another one, ergo we should track dependencies).
