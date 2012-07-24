#!/usr/bin/python
# encoding: utf8

__version__ = "0.0.0"
__author__ = "Martin Sivak <mars@montik.net>"

import urwid
import urwid.raw_display
import urwid.web_display
import model
import app


def e(w):
    return urwid.AttrWrap(w, "editbx", "editfc")

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

class PartEditor(app.UIScreen):
    def __init__(self, a, store, partlist = None):
        app.UIScreen.__init__(self, a, store)
        self._partlist = partlist
        self._save = []

    def show(self, args = None):
        self._save = []
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
        if self.store.of(self._source) is None:
            self.store.add(self._source)
        self.store.commit()
        self.close()
            
    def input(self, key):
        if key == 'esc':
            self.close()

class NewPartList(app.UIScreen):
    def __init__(self, a, store, source):
        app.UIScreen.__init__(self, a, store)
        self._source = source

        w = urwid.Columns([
            ("weight", 2, urwid.Text(u"name")),
            ("fixed", 10, urwid.Text(u"footprint")),
            ("weight", 1, urwid.Text(u"manufacturer")),
            ("fixed", 10, urwid.Text(u"sku")),
            ("fixed", 6, urwid.Text(u"count")),
            ("fixed", 6, urwid.Text(u"$$")),
            ], 3)

        buttons = urwid.Columns([
            ("fixed", 16, urwid.Button(u"Přidat řádek", self.add)),
            ("fixed", 16, urwid.Button(u"Další krok", self.save)),
            urwid.Divider(u" ")
            ], 3)


        self.walker = urwid.SimpleListWalker([w, buttons])
        self.parts = []

    def _newpart(self):
        p = {
            "name": u"",
            "footprint": u"",
            "manufacturer": u"",
            "sku": u"",
            "count": 0,
            "unitprice": 0,
            "source": self._source
            }
        return p

    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "editbx", "editfc")
        w = urwid.Columns([
            ("weight", 2, p(urwid.Edit(unicode(s["name"])))),
            ("fixed", 10, p(urwid.Edit(unicode(s["footprint"])))),
            ("weight", 1, p(urwid.Edit(unicode(s["manufacturer"])))),
            ("fixed", 10, p(urwid.Edit(unicode(s["sku"])))),
            ("fixed", 6, p(urwid.IntEdit(unicode(s["count"])))),
            ("fixed", 6, p(urwid.Edit(unicode(s["unitprice"])))),
            ], 3)
        w._data = s
        return w

    def show(self, args = None):
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def add(self, signal, args = None):
        p = self._newpart()
        self.parts.append(p)

        buttons = self.walker.pop()
        self.walker.append(self._entry(p))
        self.walker.append(buttons)
        self.walker.set_focus(len(self.walker) - 2)

    def save(self, signal, args = None):
        pass

    def input(self, key):
        if key == 'esc':
            self.close()

class SourceSelector(app.UIScreen):
    def __init__(self, a, store):
        app.UIScreen.__init__(self, a, store)

    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "body", "editfc")
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
        if key == 'esc':
            self.close()
        elif key == "n":
            new_source = SourceEditor(self.app, self.store)
            self.app.switch_screen_with_return(new_source)
        elif key == "e":
            widget, id = self.walker.get_focus()
            source = SourceEditor(self.app, self.store, widget._data)
            self.app.switch_screen_with_return(source)
        elif key == "enter":
            widget, id = self.walker.get_focus()
            w = NewPartList(self.app, self.store, widget._data)
            self.app.switch_screen_with_return(w)

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
        self._save = []

    def show(self, args = None):
        self._save = []
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
        if self.store.of(self._source) is None:
            self.store.add(self._source)
        self.store.commit()
        self.close()
            
    def input(self, key):
        if key == 'esc':
            self.close()

def main():
    store = model.getStore("sqlite:shelves.sqlite3")
    text_header = "Shelves 0.0.0"
    a = app.App(text_header)

    source_screen = SourceSelector(a, store)
    a.switch_screen_modal(source_screen)

if '__main__'==__name__ or urwid.web_display.is_web_request():
    main()
