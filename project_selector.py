import app
import urwid
import model
from selector import ItemSelector
from part_selector import SearchForParts

class ItemAssigner(app.UIScreen):
    def __init__(self, a, store):
        app.UIScreen.__init__(self, a, store)

class ProjectEditor(app.UIScreen):
    def __init__(self, a, store, source = None):
        app.UIScreen.__init__(self, a, store)
        if source is None:
            source = model.Project(
                name = u"",
                summary = u"",
                description = u""
                )
        self._source = source
        self._save = app.SaveRegistry()

    def show(self, args = None):
        self._save.clear()
        listbox_content = [
            urwid.Edit(u"Název", self._source.name or u"").bind(self._source, "name").reg(self._save),
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

class ProjectSelector(ItemSelector):
    EDITOR = ProjectEditor
    MODEL = model.Project

    def select(self, widget, id):
        return SearchForParts(self.app, self.store, action = ItemAssigner, action_kwargs = {"project": widget._data})
