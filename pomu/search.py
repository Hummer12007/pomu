from enum import Enum
from pydoc import pager

from curtsies import FullscreenWindow, fmtstr, fsarray
from curtsies.fmtfuncs import invert

from pomu.util.iquery import Prompt, clamp

class Entry:
    def __init__(self, item, source, children=None):
        self.expanded = False
        self._source = source
        self.item = item
        self.children = children

    def toggle(self, idx=0):
        if idx == 0:
            self.expanded = not self.expanded
        else:
            child = self.children[idx - 1]
            self.children[idx - 1] = (not child[0], child[1])
        if self.expanded and not self.children:
            self.children = [(False, x) for x in self._source.list_items(self.item[0])]

    def get_idx(self, idx):
        return ((self, None if idx == 0 or not self.children else self.children[idx-1]))

    def __len__(self):
        return len(self.children) + 1 if self.expanded else 1

    def selected(self):
        if self.children:
            return [child[1] for child in self.children if child[0]]
        return []

class PromptState(Enum):
    TOP_PREV=0
    TOP_OK=1
    LIST=2

class PSPrompt(Prompt):
    def __init__(self, source):
        super().__init__([])
        self.data = source
        self.page_count = self.data.page_count()
        self.pages = {}
        self.state = PromptState.LIST
        self.set_page(1)

    def results(self):
        # (cp, v, overlay, data)
        res = []
        for k, v in self.pages.items():
            for entry in v:
                cp = entry.item[0]
                for child in entry.selected():
                    cid, v, overlay = child
                    data = self.data.get_item(cid)
                    res.append((cp, v, overlay, data))
        return res


    def set_page(self, page):
        self.idx = 0
        self.page = page
        if page in self.pages:
            self.entries = self.pages[page]
        else:
            self.entries = [self.process_entry(x) for x in self.data.get_page(page)]
            self.pages[page] = self.entries

    def render(self):
        title = str(self.page) + '//' + str(self.state.value)
        if self.page > 1:
            title = ('[ ' +
                    (invert('Prev') if self.state == 0 else ('Prev')) +
                    ' ] ' + title)
        if self.page < self.page_count:
            title = (title + ' [ ' +
                    (invert('Next') if self.state == 1 else ('Next')) +
                    ' ]')
        title = self.center(title)
        bottom = '[ ' + (invert('OK') if self.idx == len(self) else 'OK') + ' ]'
        bottom = self.center(bottom)
        items = [self.render_entry(e, idx) for idx, e in enumerate(self.lens())]
        output = fsarray([title] + items + [bottom])
        self.window.render_to_terminal(output)

    def _refresh(self):
        w, h = self.window.width, self.window.height
        output = fsarray([' ' * w] * h)
        self.window.render_to_terminal(output)

    def render_entry(self, entry, idx):
        winw = self.window.width
        if entry[1]:
            hld, data = entry[1]
            stt = '*' if hld else ' '
            text = '     [' + (invert(stt) if idx == 0 else stt) + '] '
            text += '{}::{}'.format(data[1], data[2])
        elif entry[0]:
            data = entry[0].item
            exp = 'v' if entry[0].expanded else '>'
            text = '[' + (invert(exp) if idx == 0 else exp) + '] '
            text += data[0] + ' '
            strw = fmtstr(text).width
            insw = fmtstr(data[1]).width
            text += data[1][:winw - strw - 2] + ('..' if insw + strw > winw else data[1])
        else:
            text = ''
        return text

    def process_event(self, event):
        res = super().process_event(event)
        if res:
            return res
        elif event == '<TAB>':
            self.state = PromptState((self.state.value + 1) % 2)
        elif event in {'<Ctrl-j>', '<Ctrl-m>'}:
            if self.state.value < 2:
                return -1
        else:
            return False
        return True


    def __len__(self):
        return sum(len(y) for y in self.entries)

    def center(self, stri):
        tw = fmtstr(stri).width
        pw = (self.window.width - tw) // 2
        return  ' ' * pw + stri + ' ' * pw

    def clamp(self, x):
        return clamp(x, 0, len(self))

    def toggle(self):
        item, idx = self.get_idx(self.idx)
        item[0].toggle(idx)

    def preview(self):
        target = self.get_target()
        if target[1]:
            data = self.data.get_item(target[1][1][0])
            pager(data)
            self._refresh()
        self.render()
    
    def lens(self):
        h = self.window.height - 2
        lst = [self.get_idx(i)[0] for i in range(self.idx, self.clamp(self.idx + h))]
        lst += [(None, None)] * clamp(h - len(lst), 0, h)
        return lst

    def get_target(self):
        return self.get_idx(self.idx)[0]

    def get_idx(self, idx):
        for entry in self.entries:
            if len(entry) > idx:
                break
            idx -= len(entry)
        return (entry.get_idx(idx), idx)

    def process_entry(self, item):
        return Entry(item, self.data)

    def run(self):
        return super().run(FullscreenWindow, hide_cursor=True)
