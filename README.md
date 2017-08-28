# Pomu

## Prerequisites

pomu requires the following packages to be installed:

- sys-apps/portage	 : Portage repository querying and management
- app-portage/repoman	 : Manifest generation
- dev-python/click	 : CLI implementation
- dev-python/git-python	 : Git repository management and initialization
- dev-python/pbraw	 : A library to fetch plaintexts from pastebins
- dev-python/curtsies	 : Curse-like terminal wrapper, used for TUIs (both fullscreen and inline) 

In addition to the necessary dependencies, pomu requires a git ebuild repository (optionally set up with portage), though it can create a new one as well (with or without setting it up in portage).

## Usage

Usage: pomu [OPTIONS] COMMAND [ARGS]...

  A utility to import and manage ebuilds portage overlays

Options:
  --no-portage      Do not setup the portage repo
  --repo-path TEXT  Path to the repo directory (used with --no-portage)
  -h, --help        Show this message and exit.

Commands:
  commit     Commit user changes
  fetch      Fetch a package into a directory (or display...
  import     Import a package into a repository
  init       Initialise a pomu repository
  patch      Patch an existing package
  search     Search gpo.zugaina.org
  show       Display installed package info
  status     Display pomu status
  uninstall  Uninstall a package

## Done work (for GSOC)

During the summer coding period the following projects were implemented (from scratch):

- The `pomu` utility (in this repository)
- The `pbraw` library (and utility) to fetch plaintexts from arbitrary pastebin services (see https://github.com/Hummer12007/pbraw)

## Planned functionality

- [x] create/use a git repository/directory, in a configurable location (default may be /usr/local/portage),
with an option to set it up as a repo in /etc/portage/repos.conf;

- [ ] import ebuilds and related files (FILESDIR, eclasses, dependent ebuilds (if required) etc.) in atomic
commits with meaningful descriptions;
  - [x] ebuilds
  - [ ] FILESDIR (imports all the files, relevant import is WIP)
  - [ ] dependent ebuilds
  - [x] atomic commits
  - [x] commit message generation
  
- [ ] import packages from:
  - [x] the portage tree (repositories set up in portage)
  - [x] overlays (either in fs or in remote repositories, including, but not limited to, overlays in the layman
catalog, arbitrary git repos (with proper layout) etc.)
  - [x] local/remote text files
  - [x] (possibly) some sane pastebin services (like github gists, paste.pound-python.org etc.);
  - [x] bugzilla tickets (from ebuild/patch attachments, and (optionally) from links in comments (at least (may
be extended) serving text/plain content))
  - [ ] github pull requests (may be extended to support repos other than gentoo/gentoo) (backend is practically done, only thing left's to hook it up to GH, so 70% done)

4) when importing packages:
  - [ ] (from overlays) detect dependencies/eclasses unique to the overlay (unavailable in parent overlays/main
tree) and (prompt the user to) import them (WIP)
  - [x] (from overlays/portage) detect user changes and merge remote changes hunk by hunk (in a manner
similar to dispatch-conf) (not tested enough)
  - [x] allow the user to specify package category/name (when importing from files/pastebins/patches, and new
package version
  - [x] generate required files (Manifests etc.)

- [x] search for packages, interfacing with gpo.zugaina.org;

- [ ] update ebuilds pulled in from portage/overlays, merging upstream and user changes; (work on patch sequences and reordering complete, 30% done)

- [x] remove packages from the repository (if possible, by simply reverting the relevant commits, unless some
non-leaf packages/eclasses pulled in by the package are required for another one, ergo we should track dependencies).

### TODO (future plans)

- migrate from curtsies to a custom TUI library (with widgets and stuff)
- generify handlers (?)
- expand and extend global options
- properly sanitize user input
