# encoding: utf8

import model
import urwid
import app

from part_selector import SearchForParts

class GenericEditor(app.UIScreen):
    MODEL = model.Project

    def __init__(self, a, store, item = None, caller = None):
        app.UIScreen.__init__(self, a, store)
        if item is None:
            item = self.MODEL()
            item.name = u""
            item.summary = u""
            item.description = u""

        self._caller = caller
        self._item = item
        self._save = app.SaveRegistry()

    def show(self, args = None):
        self._save.clear()
        listbox_content = [
            urwid.Edit(u"Název: ", self._item.name or u"").bind(self._item, "name").reg(self._save),
            urwid.Edit(u"Krátký popis: ", self._item.summary or u"").bind(self._item, "summary").reg(self._save),
            urwid.Text(u"Popis: "),
            urwid.Edit(u"", self._item.description or u"", multiline=True).bind(self._item, "description").reg(self._save),
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

        if self.store.of(self._item) is None:
            self.store.add(self._item)
        self.store.commit()
        self.close()

class GenericSelector(app.UIScreen):
    EDITOR = None
    MODEL = None
    MODEL_ARGS = []
    ACTION = None

    def __init__(self, a, store):
        app.UIScreen.__init__(self, a, store)

    def _header(self):
        w = urwid.Columns([
            ("fixed", 15, urwid.Text(u"název")),
            urwid.Text(u"shrnutí")
            ], 3)
        return w

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
        find_args = self.conditions
        if self.MODEL_ARGS:
            find_args.extend(self.MODEL_ARGS)
        listbox_content = [self._header()] + [self._entry(p) for p in self.store.find(self.MODEL, *find_args)]
        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def input(self, key):
        if key == "n":
            new_project = self.EDITOR(self.app, self.store, caller = self)
            self.app.switch_screen_with_return(new_project)
        elif key == "e":
            widget, id = self.walker.get_focus()
            project = self.EDITOR(self.app, self.store, widget._data, caller = self)
            self.app.switch_screen_with_return(project)
        elif key == "d":
            widget, id = self.walker.get_focus()
            self.store.remove(widget._data)
            self.store.commit()
            self.app.switch_screen(self)
        elif key == "enter":
            widget, id = self.walker.get_focus()
            w = self.select(widget, id)
            self.app.switch_screen_with_return(w)
        else:
            return key

    def select(self, widget, id):
        return SearchForParts(self.app, self.store, action = self.ACTION)

    @property
    def conditions(self):
        return []
