# encoding: utf8

import model
import urwid
import app
from app import Edit, IntEdit, CheckBox, Button
from edit import DateEdit
import copy

class GenericKeybindings(dict):
    def __add__(self, added):
        d = copy.copy(self)
        d.update(added)
        return d

class GenericInterface(app.UIScreen):
    #KEYS: key -> title, method, f(self) -> bool
    KEYS = GenericKeybindings({
        "enter": (_(u"select"), "select", lambda self: True)
        })

    ALWAYS = lambda self: True
    REFRESH = True

    def __init__(self, a, store):
        app.UIScreen.__init__(self, a, store)
        self._save = app.SaveRegistry()
        self.walker = None
        self.focus = None

    def _val(self, s, name):
        for p in name.split("."):
            s = getattr(s, p)
            if s is None:
                break
        return s

    def select(self, widget, id):
        pass

    def details(self, args = None):
        return []

    def header(self, args = None):
        return []

    def rows(self, args = None):
        return []

    def show(self, args = None):
        self._save.clear()
        listbox_content = []
        listbox_content.extend(self.header(args))
        listbox_content.extend(self.rows(args))
        listbox_content.extend(self.details(args))

        self.walker = urwid.SimpleListWalker(listbox_content)
        if self.focus:
            self.walker.set_focus(self.focus)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        w,h = self.app.screen.get_cols_rows()

        return urwid.Padding(self.body, width = w - 2, align = "center")

    def input(self, key):
        if key in self.KEYS and self.KEYS[key][2](self):
            widget, id = self.walker.get_focus()
            w = getattr(self, self.KEYS[key][1])(widget, id)
            if w == self.REFRESH:
                self.app.switch_screen(self)
                return True
            elif w is None:
                return True
            elif w == False:
                return key
            else:
                self.focus = id
                self.app.switch_screen_with_return(w)
                return True

        else:
            return key

class GenericEditor(GenericInterface):
    MODEL = model.Project
    FIELDS = [
        (_(u"Name: "), "name", Edit, {}, u""),
        (_(u"Summary: "), "summary", Edit, {}, u""),
        (_(u"Description: "), "description", Edit, {"multiline": True}, u""),
        ]

    def __init__(self, a, store, item = None, caller = None, save_closes = True):
        GenericInterface.__init__(self, a, store)
        if item is None:
            item = self.MODEL()
            item.name = u""
            item.summary = u""
            item.description = u""

        self._caller = caller
        self._item = item
        self._save_closes = save_closes

    def rows(self, args = None):
        listbox_content = []

        def _e(w):
            return urwid.AttrWrap(w, "edit", "edit_f")

        maxlen = max([len(f[0]) for f in self.FIELDS if not "multiline" in f[3]])

        for title, attr, edit, args, default in self.FIELDS:
            val = self._val(self._item, attr)
            if val is None:
                val = default

            if "multiline" in args:
                listbox_content.extend([
                    urwid.Text(title),
                    _e(edit(u"", val, **args).bind(self._item, attr).reg(self._save))
                    ])
            else:
                listbox_content.append(urwid.Columns([
                    ("fixed", maxlen, urwid.Text(title)),
                    _e(edit(u"", val, **args).bind(self._item, attr).reg(self._save))
                    ], 3))

        listbox_content += [
            urwid.Divider(u" "),
            Button(_(u"Save"), self.save)
            ]

        return listbox_content


    def save(self, signal, args = None):
        for w in self._save:
            w.save()

        if self.store.of(self._item) is None:
            self.store.add(self._item)

        self.pre_commit_hook(self._item)
        self.store.commit()

        if self._save_closes:
            self.close()

    def pre_commit_hook(self, item):
        pass

class GenericBrowser(GenericInterface):
    MODEL = None
    MODEL_ARGS = []
    FIELDS = [
        (_(u"name"), "weight", 1, "name"),
        (_(u"summary"), "weight", 3, "summary")
        ]
    SORT = True
    EDITOR = None
    SEARCH_FIELDS = ["name", "summary", "description"]

    KEYS = GenericInterface.KEYS + {
        "e": (_(u"edit"), "edit", lambda self: self.EDITOR)
        }


    def __init__(self, a, store, search = None):
        GenericInterface.__init__(self, a, store)
        self.order_by = None
        self.order_desc = False
        self.search = search

    def header(self, args = None):
        w = urwid.Columns([(f[1], f[2], urwid.Text(f[0])) for f in self.FIELDS], 2)
        return [w]

    def _entry(self, s):
        p = lambda w: urwid.AttrMap(w, "body", "list_f")
        def _prep(f):
            val = self._val(s, f[3])
            if isinstance(val, bool) and val == True:
                return _(u"[x]")
            elif isinstance(val, bool) and val == False:
                return _(u"[ ]")
            elif val is None:
                return _(u"-")
            else:
                return unicode(val)

        w = p(urwid.Columns([(f[1], f[2], urwid.Text(_prep(f))) for f in self.FIELDS], 2))
        w = app.Selectable(w)
        w._data = s
        return w

    def rows(self, args = None, decorator = _entry):
        return [decorator(self, p) for p in self.content]

    def show(self, args = None):
        self.order_by = args
        return GenericInterface.show(self, args)

    def input(self, key):
        if GenericInterface.input(self, key) == True:
            return True

        elif self.SORT:
            try:
                col = int(key) - 1
                f = self.FIELDS[col][3]
                self.focus = None
                self.app.switch_screen(self, f)
                return True
            except (TypeError, ValueError, KeyError, IndexError):
                pass

        return key

    def edit(self, widget, id):
        editor = self.EDITOR(self.app, self.store, item = widget._data, caller = self)
        return editor

    @property
    def footer(self):
        """Method called after show, returns new window footer."""
        keys = [u"%s - %s" % (k,v[0]) for k,v in self.KEYS.iteritems() if v[2](self)]
        keys.append(_("<number> - sort column"))
        return u", ".join(keys)

    @property
    def title(self):
        p = [_(u"List of parts")]
        if self.search:
            p.append(_(u"which contain '%s'") % self.search)
        return u" ".join(p)

    @property
    def content(self, args=None):
        find_args = self.conditions

        if self.MODEL_ARGS:
            find_args.extend(self.MODEL_ARGS)

        res = self.store.find(self.MODEL, *find_args)
        if self.order_by:
            try:
                # try sorting only if it is DB column
                f = self._val(self.MODEL, self.order_by)
                if isinstance(f, model.SortableBase):
                    res.order_by(f)
            except AttributeError:
                pass
        return res

    @property
    def conditions(self):
        find_args = []

        if self.search:
            for term in self.search.split():
                find_args.append(model.Or([
                    getattr(self.MODEL, f).like(u"%%%s%%" % term, "$", False)
                    for f in self.SEARCH_FIELDS
                    ]))

        return find_args

class GenericSelector(GenericBrowser):
    ACTION = None
    KEYS = GenericBrowser.KEYS + {
        "a": (_(u"add new"), "add", lambda s: True),
        "d": (_(u"delete"), "remove", lambda s: True)
        }

    def remove(self, widget, id):
        self.store.remove(widget._data)
        self.store.commit()
        return self.REFRESH

    def add(self, widget, id):
        return self.EDITOR(self.app, self.store, None, caller = self)
