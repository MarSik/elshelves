# encoding: utf8

import app
import urwid
import model
from selector import GenericSelector, GenericEditor
from part_selector import SearchForParts

class ItemAssigner(app.UIScreen):
    def __init__(self, a, store, partlist, item, back=None):
        app.UIScreen.__init__(self, a, store, back)
        self._item = item
        self._partlist = partlist

    def show(self, args=None):
        # run all model pre-check verifiers
        errors = self.verify()
        if errors:
            self.back(errors[0])
        else:
            try:
                self.save()
                self.close()
            except Exception, e:
                self.back(0)

    def verify(self):
        return None

    def save(self):
        try:
            # save all data to db - completeness checking is done in model
            # verification methods
            for part in self._partlist:
                assert part.part_type is not None

                # known part, just assign new amount request of it
                if int(part.count) > 0:
                    new_part = model.Assignment()
                    new_part.part_type = part.part_type
                    new_part.item = self._item
                    new_part.count = int(part.count)
                    self.store.add(new_part)

            self.store.commit()
        except Exception:
            self.store.rollback()
            raise


class AssignmentSelector(GenericSelector):
    MODEL = model.Assignment
    EDITOR = None

    def __init__(self, a, store, item):
        GenericSelector.__init__(self, a, store)
        self._item = item

    def _header(self):
        w = urwid.Columns([
            ("fixed", 15, urwid.Text(u"typ")),
            ("fixed", 10, urwid.Text(u"pouzdro")),
            urwid.Text(u"shrnutí"),
            ("fixed", 15, urwid.Text(u"výrobce")),
            ("fixed", 6, urwid.Text(u"přiř.")),
            ("fixed", 6, urwid.Text(u"žádáno"))
            ], 3)
        return w

    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "body", "editfc_f")
        w = p(urwid.Columns([
            ("fixed", 15, urwid.Text(unicode(s.part_type.name))),
            ("fixed", 10, urwid.Text(unicode(s.part_type.footprint.name))),
            urwid.Text(s.part_type.summary),
            ("fixed", 15, urwid.Text(unicode(s.part_type.manufacturer))),
            ("fixed", 6, urwid.Text(unicode(s.parts.find().sum(model.Part.count)))),
            ("fixed", 6, urwid.Text(unicode(s.count)))
            ], 3))
        w = app.Selectable(w)
        w._data = s
        return w

    @property
    def conditions(self):
        return [self.MODEL.item == self._item]

    @property
    def project(self):
        return self._project

    def add(self):
        return SearchForParts(self.app, self.store, action = ItemAssigner, action_kwargs = {"item": self._item})

    def edit(self, widget, id):
        return None

    def select(self, widget, id):
        # todo select the part pile to get parts from
        pass

class ItemEditor(GenericEditor):
    MODEL = model.Item

    def __init__(self, a, store, item = None, caller = None):
        if item is None:
            item = self.MODEL()
            item.kit = False
            item.serial = u""
            item.description = u""
            item.project = caller.project
            item.history = History()
            item.history.event = History.NEW

        GenericEditor.__init__(self, a, store, item)

    def show(self, args = None):
        self._save.clear()
        listbox_content = [
            urwid.Edit(u"Sériové č.", self._item.serial or u"").bind(self._item, "serial").reg(self._save),
            urwid.CheckBox(u"Kit", self._item.kit or False).bind(self._item, "kit").reg(self._save),
            urwid.Text(u"Popis"),
            urwid.Edit(u"", self._item.description or u"", multiline=True).bind(self._item, "description").reg(self._save),
            urwid.Divider(u" "),
            urwid.Button(u"Uložit", self.save)
            ]
        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

class ItemSelector(GenericSelector):
    EDITOR = ItemEditor
    MODEL = model.Item

    def __init__(self, a, store, project):
        GenericSelector.__init__(self, a, store)
        self._project = project

    def _header(self):
        w = urwid.Columns([
            ("fixed", 5, urwid.Text(u"id")),
            ("fixed", 20, urwid.Text(u"sériové číslo")),
            urwid.Text(u"forma"),
            ("fixed", 20, urwid.Text(u"změněno")),
            ("fixed", 20, urwid.Text(u"vytvořeno"))
            ], 3)
        return w

    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "body", "editfc_f")

        if s.kit:
            kit = u"kit"
        else:
            kit = u""

        oldest = s.history
        while oldest.parent:
            oldest = oldest.parent

        w = p(urwid.Columns([
            ("fixed", 5, urwid.Text(unicode(s.id))),
            ("fixed", 20, urwid.Text(unicode(s.serial))),
            urwid.Text(kit),
            ("fixed", 20, urwid.Text(unicode(s.history.time))),
            ("fixed", 20, urwid.Text(unicode(oldest.time)))
            ], 3))
        w = app.Selectable(w)
        w._data = s
        return w

    @property
    def conditions(self):
        return [self.MODEL.project == self._project]

    @property
    def project(self):
        return self._project

    def select(self, widget, id):
        return AssignmentSelector(self.app, self.store, item = widget._data)

class ProjectEditor(GenericEditor):
    MODEL = model.Project

class ProjectSelector(GenericSelector):
    EDITOR = ProjectEditor
    MODEL = model.Project

    def select(self, widget, id):
        return ItemSelector(self.app, self.store, project = widget._data)
