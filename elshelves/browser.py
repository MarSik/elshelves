# encoding: utf8

import app
import model
import urwid
from selector import GenericBrowser

class HistoryBrowser(GenericBrowser):
    MODEL = None
    MODEL_ARGS = []
    FIELDS = [
        (_(u"time"), "fixed", 20, "time"),
        (_(u"event"), "fixed", 2, "event"),
        (_(u"location"), "fixed", 10, "location"),
        (_(u"description"), "weight", 2, "description")
        ]
    SORT = False

    def __init__(self, a, store, history = None):
        GenericBrowser.__init__(self, a, store)
        self._history = []
        while history:
            self._history.append(history)
            history = history.parent

    @property
    def content(self, args = None):
        return self._history

    @property
    def title(self):
        return _(u"History")

class PartBrowser(GenericBrowser):
    MODEL = model.Part
    EDITOR = False

    FIELDS = [
        (_(u"date"), "fixed", 10, "date"),
        (_(u"source"), "weight", 1, "source.name"),
        (_(u"price"), "fixed", 10, "price"),
        (_(u"count"), "fixed", 6, "count"),
        (_(u"assigned"), "fixed", 5, "assigned")
        ]

    def __init__(self, a, store, assignment = None, part_type = None, unusable = False):
        GenericBrowser.__init__(self, a, store)
        self._assignment = assignment
        self._part_type = part_type
        self._unusable = unusable

    @property
    def conditions(self):
        conds = [model.Or(self.MODEL.assignment == self._assignment, self.MODEL.assignment == None)]
        if self._assignment:
            conds.append(self.MODEL.part_type == self._assignment.part_type)
        if self._part_type:
            conds.append(self.MODEL.part_type == self._part_type)
        if not self._unusable:
            conds.append(self.MODEL.usable == True)

        return conds

    def select(self, widget, id):
        return HistoryBrowser(self.app, self.store, history = widget._data.history)

    @property
    def title(self):
        s = _("Parts")
        if self._part_type:
            s += _(u" of type %s (%s)") % (self._part_type.name, self._part_type.manufacturer)
        elif self._assignment:
            s += _(u" of type %s (%s)") % (self._assignment.part_type.name, self._assignment.part_type.manufacturer)

        if self._assignment:
            s += _(u" assignable to no. %s in %s") % (self._assignment.item.serial,
                                                     self._assignment.item.project.name)
        return s

    def input(self, key):
        if self.EDITOR and key == "e":
            widget, id = self.walker.get_focus()
            self.edit(widget, id)
            return True
        else:
            return GenericBrowser.input(self, key)

    @property
    def footer(self):
        """Method called after show, returns new window footer."""
        if self.EDITOR:
            return _("ENTER - select, E - edit")
        else:
            return _("ENTER - select")

class Browser(GenericBrowser):
    MODEL = model.PartType
    FIELDS = [
        (_(u"name"), "fixed", 15, "name"),
        (_(u"summary"), "weight", 1, "summary"),
        (_(u"manufacturer"), "weight", 1, "manufacturer"),
        (_(u"pins"), "fixed", 6, "pins"),
        (_(u"footprint"), "fixed", 10, "footprint.name"),
        (_(u"count"), "fixed", 6, "count")
        ]

    def select(self, widget, id):
        return PartBrowser(self.app, self.store, assignment = None, part_type = widget._data)
