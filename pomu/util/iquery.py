"""A module to interactively query"""
from pydoc import pager

from curtsies import CursorAwareWindow, Input, fsarray, fmtstr
from curtsies.fmtfuncs import invert
from pbraw import grab


class Position:
    def __init__(self, row=0, column=0):
        self.row = row
        self.column = column

def clamp(x, m, M):
    return max(m, min(x, M))

def render_entry(entry, width, active=False):
    # (name, contents, state, value)
    char = '*' if entry[2] else ' '
    w = 3 + fmtstr(entry[0]).width + 2
    if entry[3]:
        text = fmtstr(entry[3])
        val = entry[3][:width - w - 2] + '..' if text.width < width - w else entry[3]
    else:
        val = ''
    return fmtstr(
            '[' + (invert(char) if active else char) + '] ' +
            entry[0] + ' ' + val)

def process_entry(entry):
    if isinstance(entry, str):
        return (entry[0], None, False, None)
    return (entry[0], entry[1], False, entry[0] if entry[0].endswith('.ebuild') else 'files/{}'.format(entry[0]))

class Prompt:
    def __init__(self, entries):
        self.entries = [process_entry(x) for x in entries]
        self.idx = 0
        self.text = ''
        self.list = True
        self.cursor_pos = Position()

    def run(self):
        with open('/dev/tty', 'r') as tty_in, \
             open('/dev/tty', 'w') as tty_out, \
             Input(in_stream=tty_in) as input_, \
             CursorAwareWindow(in_stream=tty_in,
                               out_stream=tty_out,
                               hide_cursor=False,
                               extra_bytes_callback=input_.unget_bytes) as window:
            self.window = window
            self.render()
            for event in input_:
                if self.process_event(event) == -1:
                    break
                self.render()
        return [(x[0], x[1], x[3]) for x in self.entries if x[2]]

    def clamp(self, x):
        return clamp(x, 0, len(self.entries))

    def preview(self):
        entry = self.entries[self.idx]
        if entry[0] is not None:
            pager(entry[1])
        else:
            gr = grab(entry)
            if not gr:
                del self.entries[self.idx]
                self.idx = self.clamp(self.idx - 1)
                pager('Error: could not fetch '.format(entry))
            self.entries[self.idx:self.idx+1] = [process_entry((x[0], x[1].encode('utf-8'))) for x in gr]
            pager(self.entries[self.idx][1])

    def toggle(self):
        if self.idx == len(self.entries):
            return
        e = self.entries[self.idx]
        self.entries[self.idx] = (e[0], e[1], not e[2], e[3])

    def process_event(self, event):
        if self.list:
            if event == '<UP>':
                self.idx = self.clamp(self.idx - 1)
            elif event == '<DOWN>':
                self.idx = self.clamp(self.idx + 1)
            elif event == '<SPACE>':
                self.toggle()
            elif event in {'p', 'P'}:
                self.preview()
            elif event in {'<ESC>', '<Ctrl-g>'}:
                return -1
            elif event in {'e', '<Ctrl-j>', '<Ctrl-m>'}:
                self.list = False
                if self.idx == len(self.entries):
                    return -1
                self.cursor_pos.column = fmtstr(self.entries[self.idx][3]).width
        else:
            if event in {'<ESC>', '<Ctrl-g>'}:
                self.list = True
            if event == '<BACKSPACE>':
                self.delete_cur_char()
            elif event == '<SPACE>':
                self.add_char(' ')
            elif event == '<HOME>':
                self.cursor_pos.column = 0
            elif event == '<END>':
                self.cursor_pos.column = fmtstr(self.entries[self.idx][3]).width
            elif event == '<LEFT>':
                self.cursor_pos.column = clamp(self.cursor_pos.column - 1,
                        0, fmtstr(self.entries[self.idx][3]).width)
            elif event == '<RIGHT>':
                self.cursor_pos.column = clamp(self.cursor_pos.column + 1,
                        0, fmtstr(self.entries[self.idx][3]).width)
            elif event in {'<Ctrl-j>', '<Ctrl-m>'}:
                self.list = True
            elif isinstance(event, str) and not event.startswith('<'):
                self.add_char(event)

    def render(self):
        if self.list:
            output = fsarray(
                [render_entry(x, self.window.width, i == self.idx) for i, x in enumerate(self.entries)] +
                [' [ ' + 
                    ('OK' if self.idx < len(self.entries) else invert('OK')) +
                    ' ] '], width=self.window.width)
            self.window.render_to_terminal(output)
            return
        self.cursor_pos.row = 1
        cur = self.entries[self.idx]
        output = fsarray(['Please provide value for {}'.format(cur[0]), cur[3]], width=self.window.width)
        self.window.render_to_terminal(output, (self.cursor_pos.row, self.cursor_pos.column))

    def add_char(self, char):
        e = self.entries[self.idx]
        p = self.cursor_pos.column
        self.entries[self.idx] = (e[0], e[1], e[2], e[3][:p] + char + e[3][p:])
        self.cursor_pos.column += 1

    def delete_cur_char(self):
        e = self.entries[self.idx]
        p = self.cursor_pos.column
        if e[3]:
            self.entries[self.idx] = (e[0], e[1], e[2], e[3][:p - 1] + e[3][p:])
            self.cursor_pos.column -= 1
