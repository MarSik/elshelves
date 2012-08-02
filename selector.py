# encoding: utf8

import model
import urwid
import app
from app import Edit, IntEdit, CheckBox, Button

class GenericEditor(app.UIScreen):
    MODEL = model.Project
    FIELDS = [
        (_(u"Name: "), "name", Edit, {}, u""),
        (_(u"Summary: "), "summary", Edit, {}, u""),
        (_(u"Description: "), "description", Edit, {"multiline": True}, u""),
        ]

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
        listbox_content = []

        maxlen = max([len(f[0]) for f in self.FIELDS if not "multiline" in f[3]])

        for title, attr, edit, args, default in self.FIELDS:
            if "multiline" in args:
                listbox_content.extend([
                    urwid.Text(title),
                    edit(u"", getattr(self._item, attr) or default, **args).bind(self._item, attr).reg(self._save)
                    ])
            else:
                listbox_content.append(urwid.Columns([
                    ("fixed", maxlen, urwid.Text(title)),
                    edit(u"", getattr(self._item, attr) or default, **args).bind(self._item, attr).reg(self._save)
                    ], 3))

        listbox_content += [
            urwid.Divider(u" "),
            Button(_(u"Save"), self.save)
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

class GenericBrowser(app.UIScreen):
    MODEL = None
    MODEL_ARGS = []
    FIELDS = [
        (_(u"name"), "weight", 1, "name"),
        (_(u"summary"), "weight", 3, "summary")
        ]

    def __init__(self, a, store):
        app.UIScreen.__init__(self, a, store)

    def _header(self):
        w = urwid.Columns([(f[1], f[2], urwid.Text(f[0])) for f in self.FIELDS], 3)
        return w

    def _entry(self, s):
        def _val(s, name):
            for p in name.split("."):
                s = getattr(s, p)
            return s

        p = lambda w: urwid.AttrMap(w, "body", "list_f")
        w = p(urwid.Columns([(f[1], f[2], urwid.Text(unicode(_val(s, f[3])))) for f in self.FIELDS], 3))
        w = app.Selectable(w)
        w._data = s
        return w

    def show(self, args = None):
        listbox_content = [self._header()] + [self._entry(p) for p in self.content]
        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def input(self, key):
        if key == "enter":
            widget, id = self.walker.get_focus()
            w = self.select(widget, id)
            if w:
                self.app.switch_screen_with_return(w)
                return True
        else:
            return key

    def select(self, widget, id):
        pass

    @property
    def content(self, args=None):
        find_args = self.conditions
        if self.MODEL_ARGS:
            find_args.extend(self.MODEL_ARGS)
        return self.store.find(self.MODEL, *find_args)

    @property
    def conditions(self):
        return []

class GenericSelector(GenericBrowser):
    ACTION = None
    EDITOR = None

    def input(self, key):
        if key == "a":
            w = self.add()
            if w:
                self.app.switch_screen_with_return(w)
        elif key == "e":
            widget, id = self.walker.get_focus()
            w = self.edit(widget, id)
            if w:
                self.app.switch_screen_with_return(w)
        elif key == "d":
            widget, id = self.walker.get_focus()
            self.remove(widget, id)
        else:
            return GenericBrowser.input(self, key)

    def remove(self, widget, id):
        self.store.remove(widget._data)
        self.store.commit()
        self.app.switch_screen(self)

    def add(self):
        return self.EDITOR(self.app, self.store, None, caller = self)

    def edit(self, widget, id):
        return self.EDITOR(self.app, self.store, widget._data, caller = self)
