import model
import urwid
import app

from part_selector import SearchForParts

class ItemSelector(app.UIScreen):
    EDITOR = None
    MODEL = None
    MODEL_ARGS = []
    ACTION = None

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
        listbox_content = [self._entry(p) for p in self.store.find(self.MODEL, *self.MODEL_ARGS)]
        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def input(self, key):
        if key == "n":
            new_project = self.EDITOR(self.app, self.store)
            self.app.switch_screen_with_return(new_project)
        elif key == "e":
            widget, id = self.walker.get_focus()
            project = self.EDITOR(self.app, self.store, widget._data)
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
