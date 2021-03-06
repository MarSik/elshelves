# encoding: utf8

from . import model
import urwid
from .app import Edit, IntEdit, Text, FloatEdit, DateEdit, CheckBox
from .generics import GenericBrowser, GenericEditor

class HistoryBrowser(GenericBrowser):
    MODEL = None
    MODEL_ARGS = []
    FIELDS = [
        (_(u"time"), "fixed", 20, "time"),
        (_(u"event"), "fixed", 5, "event"),
        (_(u"location"), "fixed", 10, "location"),
        (_(u"description"), "weight", 1, "description")
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
    FIELDS = [
        (_(u"date"), "fixed", 10, "date"),
        (_(u"source"), "weight", 1, "source.name"),
        (_(u"price"), "fixed", 10, "price"),
        (_(u"vat"), "fixed", 4, "vat"),
        (_(u"project"), "weight", 2, "assignment.item.project.name"),
        (_(u"serial"), "weight", 1, "assignment.item.serial"),
        (_(u"cnt"), "fixed", 5, "count"),
        (_(u"asn"), "fixed", 3, "assigned"),
        (_(u"sld"), "fixed", 3, "soldered")
        ]

    def __init__(self, a, store, assignment = None, part_type = None,
                 unusable = False, assigned = False):
        GenericBrowser.__init__(self, a, store)
        self._assignment = assignment
        self._part_type = part_type
        self._unusable = unusable
        self._assigned = assigned

    @property
    def conditions(self):
        conds = [model.Or(self.MODEL.usable,
                          self.MODEL.usable != self._unusable)]
        if not self._assigned:
            conds.append(model.Or(self.MODEL.assignment == self._assignment,
                                  self.MODEL.assignment == None))
        if self._assignment:
            conds.append(self.MODEL.part_type == self._assignment.part_type)
        if self._part_type:
            conds.append(self.MODEL.part_type == self._part_type)

        return conds

    def select(self, widget, id):
        return HistoryBrowser(self.app, self.store,
                              history = widget._data.history)

    @property
    def title(self):
        s = _("Parts")
        if self._part_type:
            s += _(u" of type %s (%s)") % (self._part_type.name,
                                           self._part_type.manufacturer)
        elif self._assignment:
            s += _(u" of type %s (%s)") % (self._assignment.part_type.name,
                                           self._assignment.part_type.manufacturer)

        if self._assignment:
            s += _(u" assignable to no. %s in %s") % (self._assignment.item.serial,
                                                     self._assignment.item.project.name)
        return s

class PartEditor(GenericEditor):
    MODEL = model.PartType
    FIELDS = [
        (_(u"Name: "), "name", Edit, {}, u""),
        (_(u"Manufacturer: "), "manufacturer", Edit, {}, u""),
        (_(u"Summary: "), "summary", Edit, {}, u""),
        (_(u"Pins: "), "footprint.pins", IntEdit, {}, u""),
        (_(u"Holes: "), "footprint.holes", IntEdit, {}, u""),
        (_(u"Footprint: "), "footprint.name", Text, {}, u""),
        (_(u"Datasheet: "), "datasheet", Edit, {}, u""),
        (_(u"Description: "), "description", Edit, {"multiline": True}, u""),
        ]

    DETAIL_FIELDS = PartBrowser.FIELDS

    def __init__(self, a, store, item = None, caller = None):
        GenericEditor.__init__(self, a, store, item, caller)
        self._browser = PartBrowser(a, store, part_type = item, assigned = True)

    def details(self, args = None):
        def _decorate_from(part_browser, o):
            o = part_browser._entry(o)
            o._from = part_browser
            return o

        return [urwid.Divider(u" ")] + \
               self._browser.header() + \
               self._browser.rows(decorator = _decorate_from)

    def select(self, widget, id):
        if hasattr(widget, "_from"):
            return widget._from.select(widget, id)
        else:
            return False

    def pre_commit_hook(self, item):
        # update records in search term table
        model.Term.register(item)

class Browser(GenericBrowser):
    MODEL = model.PartType
    FIELDS = [
        (_(u"name"), "fixed", 15, "name"),
        (_(u"summary"), "weight", 1, "summary"),
        (_(u"manuf."), "weight", 1, "manufacturer"),
        (_(u"pins"), "fixed", 6, "footprint.pins"),
        (_(u"footprint"), "fixed", 10, "footprint.name"),
        (_(u"total"), "fixed", 6, "count_w_assigned"),
        (_(u"free"), "fixed", 6, "count")
        ]
    EDITOR = PartEditor

    def __init__(self, a, store, search = None, footprint = None):
        GenericBrowser.__init__(self, a, store, search)
        self._footprint = footprint

    @property
    def conditions(self):
        conds = GenericBrowser.conditions.fget(self)
        if self._footprint:
            conds.append(self.MODEL.footprint == self._footprint)

        return conds

    def select(self, widget, id):
        return self.EDITOR(self.app, self.store,
                           item = widget._data, caller = self)

class RawPartEditor(GenericEditor):
    MODEL = model.Part
    FIELDS = [
        (_(u"Name: "), "part_type.name", Edit, {}, u""),
        (_(u"Manufacturer: "), "part_type.manufacturer", Edit, {}, u""),
        (_(u"Price: "), "price", FloatEdit, {}, u""),
        (_(u"VAT: "), "vat", FloatEdit, {}, u""),
        (_(u"Date: "), "date", DateEdit, {}, None),
        (_(u"Source: "), "source.name", Text, {}, None),
        (_(u"Assigned: "), "assignment", Text, {}, u""),
        (_(u"Soldered: "), "soldered", CheckBox, {}, False),
        (_(u"Summary: "), "part_type.summary", Edit, {}, u""),
        (_(u"Pins: "), "part_type.footprint.pins", IntEdit, {}, u""),
        (_(u"Holes: "), "part_type.footprint.holes", IntEdit, {}, u""),
        (_(u"Footprint: "), "part_type.footprint.name", Text, {}, u""),
        (_(u"Datasheet: "), "part_type.datasheet", Edit, {}, u""),
        (_(u"Description: "), "part_type.description", Edit, {"multiline": True}, u""),
        ]

    DETAIL_FIELDS = HistoryBrowser.FIELDS

    def __init__(self, a, store, item = None, caller = None):
        GenericEditor.__init__(self, a, store, item, caller)
        self._browser = HistoryBrowser(a, store, history = item.history)

    def details(self, args = None):
        def _decorate_from(part_browser, o):
            o = part_browser._entry(o)
            o._from = part_browser
            return o

        return [urwid.Divider(u" ")] + \
               self._browser.header() + \
               self._browser.rows(decorator = _decorate_from)

    def select(self, widget, id):
        if hasattr(widget, "_from"):
            return widget._from.select(widget, id)
        else:
            return False

    def pre_commit_hook(self, item):
        # update records in search term table
        model.Term.register(item.part_type)

class RawPartBrowser(Browser):
    MODEL = model.Part
    EDITOR = RawPartEditor
    FIELDS = [
        (_(u"name"), "weight", 1, "part_type.name"),
        (_(u"footpr."), "fixed", 8, "part_type.footprint.name"),
        (_(u"date"), "fixed", 10, "date"),
        (_(u"source"), "fixed", 6, "source.shortname"),
        (_(u"price"), "fixed", 6, "price"),
        (_(u"vat"), "fixed", 4, "vat"),
        (_(u"cnt"), "fixed", 5, "count"),
        (_(u"asn"), "fixed", 3, "assigned"),
        (_(u"sld"), "fixed", 3, "soldered")
        ]

    def __init__(self, a, store, unusable = False, assigned = True):
        GenericBrowser.__init__(self, a, store)
        self._unusable = unusable
        self._assigned = assigned

    @property
    def conditions(self):
        conds = [model.Or(self.MODEL.usable,
                          self.MODEL.usable != self._unusable)]
        if not self._assigned:
            conds.append(self.MODEL.assignment == None)
        return conds

    @property
    def title(self):
        s = _("Parts - raw list")
        return s

class FootprintEditor(GenericEditor):
    MODEL = model.Footprint
    FIELDS = [
        (_(u"name"), "name", Edit, {}, u""),
        (_(u"kicad"), "kicad", Edit, {}, u""),
        (_(u"summary"), "summary", Edit, {}, u""),
        (_(u"pins"), "pins", IntEdit, {}, u""),
        (_(u"holes"), "holes", IntEdit, {}, u""),
        (_(u"description"), "description", Edit, {"multiline": True}, u"")
        ]

    DETAIL_FIELDS = Browser.FIELDS

    def __init__(self, a, store, item = None, caller = None):
        GenericEditor.__init__(self, a, store, item, caller)
        self._browser = Browser(a, store, footprint = item)

    def details(self, args = None):
        def _decorate_from(part_browser, o):
            o = part_browser._entry(o)
            o._from = part_browser
            return o

        return [urwid.Divider(u" ")] + \
               self._browser.header() + \
               self._browser.rows(decorator = _decorate_from)

    def select(self, widget, id):
        if hasattr(widget, "_from"):
            return widget._from.select(widget, id)
        else:
            return False


class FootprintBrowser(Browser):
    MODEL = model.Footprint
    EDITOR = FootprintEditor
    FIELDS = [
        (_(u"name"), "fixed", 10, "name"),
        (_(u"kicad"), "fixed", 10, "kicad"),
        (_(u"summary"), "weight", 1, "summary"),
        (_(u"holes"), "fixed", 5, "holes"),
        (_(u"pins"), "fixed", 4, "pins")
        ]

    def __init__(self, a, store, part_type = None):
        GenericBrowser.__init__(self, a, store)
        self._part_type = part_type

    @property
    def conditions(self):
        conds = []
        if self._part_type:
            conds.append(model.PartType.footprint == self)
        return conds

    @property
    def title(self):
        s = _("Footprints")
        if self._part_type:
            s = _(u"Available footprints for type %s (%s)") % (self._part_type.name,
                                                               self._part_type.manufacturer)
        return s
