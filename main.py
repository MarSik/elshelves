#!/usr/bin/python
# encoding: utf8

__version__ = "0.0.0"
__author__ = "Martin Sivak <mars@montik.net>"

import urwid
import urwid.raw_display
import urwid.web_display
import model
import app

from part_selector import SearchForParts, PartSelector

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

def e(w):
    return urwid.AttrWrap(w, "editbx", "editfc")


class SourceSelector(app.UIScreen):
    def __init__(self, a, store):
        app.UIScreen.__init__(self, a, store)

    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "body", "editfc_f")
        w = p(urwid.Columns([
            ("fixed", 15, urwid.Text(unicode(s.name))),
            urwid.Text(unicode(s.summary)),
            ], 3))
        w = app.Selectable(w)
        w._data = s
        return w

    def show(self, args = None):
        listbox_content = [self._entry(s) for s in self.store.find(model.Source)]
        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def input(self, key):
        if key == "n":
            new_source = SourceEditor(self.app, self.store)
            self.app.switch_screen_with_return(new_source)
        elif key == "e":
            widget, id = self.walker.get_focus()
            source = SourceEditor(self.app, self.store, widget._data)
            self.app.switch_screen_with_return(source)
        elif key == "enter":
            widget, id = self.walker.get_focus()
            w = SearchForParts(self.app, self.store, source = widget._data)
            self.app.switch_screen_with_return(w)
        else:
            return key

class SourceEditor(app.UIScreen):
    def __init__(self, a, store, source = None):
        app.UIScreen.__init__(self, a, store)
        if source is None:
            source = model.Source(
                name = u"",
                summary = u"",
                description = u"",
                home = u"http://",
                url = u"http://.../%s"
                )
        self._source = source
        self._save = app.SaveRegistry()

    def show(self, args = None):
        self._save.clear()
        listbox_content = [
            urwid.Edit(u"Název", self._source.name or u"").bind(self._source, "name").reg(self._save),
            urwid.Edit(u"Homepage", self._source.home or u"").bind(self._source, "home").reg(self._save),
            urwid.Edit(u"Krátký popis", self._source.summary or u"").bind(self._source, "summary").reg(self._save),
            urwid.Text(u"Popis"),
            urwid.Edit(u"", self._source.description or u"", multiline=True).bind(self._source, "description").reg(self._save),
            urwid.Divider(u" "),
            urwid.Button(u"Uložit", self.save)
            ]
        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def save(self, signal, args = None):
        for w in self._save:
            w.save()

        if self.store.of(self._source) is None:
            self.store.add(self._source)
        self.store.commit()
        self.close()

def main():
    store = model.getStore("sqlite:shelves.sqlite3")
    text_header = "Shelves 0.0.0"
    a = app.App(text_header)

    source_screen = SourceSelector(a, store)
    a.switch_screen_modal(source_screen)

if '__main__'==__name__ or urwid.web_display.is_web_request():
    main()
