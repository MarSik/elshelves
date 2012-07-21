#!/usr/bin/python
# encoding: utf8

__version__ = "0.0.0"
__author__ = "Martin Sivak <mars@montik.net>"

import urwid
import urwid.raw_display
import urwid.web_display
import model



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

class App(object):
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

    def __init__(self, title):
        self._setup(title)

        self._header = urwid.AttrWrap(urwid.Text(title), 'header')
        self._frame = urwid.Frame(None, header=self.header)
        
        self._footer = None
        self._screens = []

    def switch_screen(self, ui, args = None):
        self._screens.pop()
        self._screens.append((ui, args))
        self.redraw()

    def switch_screen_with_return(self, ui, args = None):
        self._screens.append((ui, args))
        self.redraw()

    def close_screen(self, scr = None):
        oldscr, oldattr = self._screens.pop()
        if scr:
            assert oldscr == scr
            
        if self._screens:
            self.redraw()
        else:
            raise urwid.ExitMainLoop()

    def redraw(self):
        screen, args = self._screens[-1]
        body = screen.show(args)
        self._frame.set_body(body)

    def run(self):
        urwid.MainLoop(self._frame, self.palette, self.screen,
                       unhandled_input=self.input).run()

    def _setup(self, title):
        urwid.web_display.set_preferences(title)
        # try to handle short web requests quickly
        if urwid.web_display.handle_short_request():
            return
        
        # use appropriate Screen class
        if urwid.web_display.is_web_request():
            screen = urwid.web_display.Screen()
        else:
            screen = urwid.raw_display.Screen()

    def input(self, key):
        """Method called to process unhandled input key presses."""
        key = self._screens[-1][0].input(key)
        if key == 'esc':
            self.close_screen()

    @property
    def header(self):
        return self._header

    @property
    def store(self):
        return self._store

    
class UIScreen(object):
    def __init__(self, app, store):
        self._app = app
        self._store = store

    def show(self, args = None):
        """Method which is called before the screen is displayed. Is has to return the top level widget containing the contents."""
        pass

    def input(self, key):
        """Method called to process unhandled input key presses."""
        pass
    
    @property
    def store(self):
        return self._store

    @property
    def app(self):
        return self._app

    def close(self):
        self.app.close_screen(self)
    
class SourceSelector(UIScreen):
    def __init__(self, app, store):
        UIScreen.__init__(self, app, store)
        
        listbox_content = [part_widget(p) for p in self.store.find(model.PartType)]
        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')
        
    def show(self, args = None):
        return self.body
    
    def input(self, key):
        if key == 'esc':
            self.close()
        elif key == "tab":
            self.walker.append(part_widget(model.PartType()))
        elif key == 'enter':
            self.store.commit()

def main():
    store = model.getStore("sqlite:shelves.sqlite3")
    text_header = "Shelves 0.0.0"
    app = App(text_header)

    source_screen = SourceSelector(app, store)
    app.switch_screen_with_return(source_screen)
    app.run()

if '__main__'==__name__ or urwid.web_display.is_web_request():
    main()
