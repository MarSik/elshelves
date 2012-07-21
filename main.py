#!/usr/bin/python
# encoding: utf8

__version__ = "0.0.0"
__author__ = "Martin Sivak <mars@montik.net>"

import urwid
import urwid.raw_display
import urwid.web_display
import model

palette = [
    ('body','black','light gray', 'standout'),
    ('reverse','light gray','black'),
    ('header','white','dark red', 'bold'),
    ('important','dark blue','light gray',('standout','underline')),
    ('editfc','white', 'dark blue', 'bold'),
    ('editbx','light gray', 'dark blue'),
    ('editcp','black','light gray', 'standout'),
    ('bright','dark gray','light gray', ('bold','standout')),
    ('buttn','black','dark cyan'),
    ('buttnf','white','dark blue','bold'),
    ]

screen = None


def e(w):
    return urwid.AttrWrap(w, "editbx", "editfc")

def save_data_cb(widget, signal, target):
    """save data "change" signal handler, target is (object, attribute) to store changed data into"""
    (obj, attr) = target

    assert type(widget.edit_text) == unicode
    
    setattr(obj, attr, widget.edit_text)

def save_data(edit, target):
    urwid.connect_signal(edit, "change", save_data_cb, target)

def part_widget(t):
    name = urwid.Edit(u"", t.name, align='left')
    save_data(name, (t, "name"))
    
    count = urwid.Text(str(t.count))

    assert type(t.summary) == unicode
    
    summary = urwid.Edit(u"", t.summary, align='left', multiline=True)
    save_data(summary, (t, "summary"))

    if t.footprint:
        fp = t.footprint.name
    else:
        fp = "undefined"
        
    pile = urwid.Pile([
        urwid.Divider(u"-"),
        e(name),
        urwid.Columns([
            e(urwid.Button(fp)),
            urwid.Columns([urwid.Text(u"Cena"), urwid.Text(str(t.price), align='left')]),
            count,
            ], 3),
        e(summary),
        ])

    pile._data = t

    return pile

class UIScreen(object):
    def __init__(self, store, frame, header, footer):
        self._store = store
        self._frame = frame
        self._header = header
        self._footer = footer
        self._result = None

    def run(self):
        self._result = None

        body = self.show()
        self._frame.set_body(body)

        urwid.MainLoop(self._frame, palette, screen,
                           unhandled_input=self.input).run()

    def show(self):
        """Method which is called before the screen is displayed. Is has to return the top level widget containing the contents."""
        pass

    def input(self, key):
        """Method called to process unhandled input key presses."""
        pass

    def close(self):
        """Exit this screen."""
        raise urwid.ExitMainLoop()

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, r):
        self._result = r

    @property
    def store(self):
        return self._store
    
class SourceSelector(UIScreen):
    def show(self):
        listbox_content = [part_widget(p) for p in self.store.find(model.PartType)]

        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        return urwid.AttrWrap(listbox, 'body')
        
    def input(self, key):
        if key == 'esc':
            self.result = self.walker.get_focus()
            self.close()
        elif key == "tab":
            walker.append(part_widget(model.PartType()))
        elif key == 'enter':
            self._store.commit()

def main():
    store = model.getStore("sqlite:shelves.sqlite3")

    text_header = "Shelves 0.0.0"
    header = urwid.AttrWrap(urwid.Text(text_header), 'header')
    full_screen = urwid.Frame(None, header=header)

    source_screen = SourceSelector(store = store,
                                   frame = full_screen,
                                   header = header,
                                   footer = None)
    source_screen.run()

def setup():
    global screen

    urwid.web_display.set_preferences("Shelves 0.0.0")
    # try to handle short web requests quickly
    if urwid.web_display.handle_short_request():
        return

    # use appropriate Screen class
    if urwid.web_display.is_web_request():
        screen = urwid.web_display.Screen()
    else:
        screen = urwid.raw_display.Screen()

    main()

if '__main__'==__name__ or urwid.web_display.is_web_request():
    setup()
