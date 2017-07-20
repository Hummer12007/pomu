from pomu.source.manager import PackageDispatcher

dispatcher = PackageDispatcher()

import pomu.source.portage
import pomu.source.file
# sealed until pbraw is released
#import pomu.source.url
#import pomu.source.bugz
