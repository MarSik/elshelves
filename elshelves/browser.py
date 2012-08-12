# encoding: utf8

import app
import model
import urwid
from app import Edit, IntEdit, Text
from selector import GenericBrowser, GenericEditor

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

class PartEditor(GenericEditor):
    MODEL = model.Part
    FIELDS = [
        (_(u"Name: "), "name", Edit, {}, u""),
        (_(u"Manufacturer: "), "manufacturer", Edit, {}, u""),
        (_(u"Summary: "), "summary", Edit, {}, u""),
        (_(u"Pins: "), "pins", IntEdit, {}, u""),
        (_(u"Footprint: "), "footprint.name", Text, {}, u""),
        (_(u"Datasheet: "), "datasheet", Edit, {}, u""),
        (_(u"Description: "), "description", Edit, {"multiline": True}, u""),
        ]


class PartBrowser(GenericBrowser):
    MODEL = model.Part
    FIELDS = [
        (_(u"date"), "fixed", 10, "date"),
        (_(u"source"), "weight", 1, "source.name"),
        (_(u"price"), "fixed", 10, "price"),
        (_(u"cnt"), "fixed", 5, "count"),
        (_(u"asn"), "fixed", 3, "assigned"),
        (_(u"sld"), "fixed", 3, "assigned")
        ]

    def __init__(self, a, store, assignment = None, part_type = None, unusable = False):
        GenericBrowser.__init__(self, a, store)
        self._assignment = assignment
        self._part_type = part_type
        self._unusable = unusable

    @property
    def conditions(self):
        conds = [model.Or(self.MODEL.usable, self.MODEL.usable != self._unusable),
                 model.Or(self.MODEL.assignment == self._assignment,
                          self.MODEL.assignment == None)]
        if self._assignment:
            conds.append(self.MODEL.part_type == self._assignment.part_type)
        if self._part_type:
            conds.append(self.MODEL.part_type == self._part_type)

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
    EDITOR = PartEditor

    def select(self, widget, id):
        return PartBrowser(self.app, self.store, assignment = None, part_type = widget._data)
