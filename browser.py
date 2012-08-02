# encoding: utf8

import app
import model
import urwid
from selector import GenericBrowser

class HistoryBrowser(GenericBrowser):
    def __init__(self, a, store, history = None):
        GenericBrowser.__init__(self, a, store)
        self._history = []
        while history:
            self._history.append(history)
            history = history.parent

    def _header(self):
        w = urwid.Columns([
            ("fixed", 20, urwid.Text(u"čas")),
            ("fixed", 2, urwid.Text(u"událost")),
            ("fixed", 20, urwid.Text(u"umístění")),
            urwid.Text(u"popis")
            ], 2)
        return w

    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "body", "editfc_f")
        w = p(urwid.Columns([
            ("fixed", 20, urwid.Text(unicode(s.time))),
            ("fixed", 2, urwid.Text(unicode(s.event))),
            ("fixed", 20, urwid.Text(unicode(u""))),
            urwid.Text(s.description or u"")
            ], 2))
        w = app.Selectable(w)
        w._data = s
        return w

    @property
    def content(self, args = None):
        return self._history

class PartBrowser(GenericBrowser):
    MODEL = model.Part
    EDITOR = None

    def __init__(self, a, store, assignment = None, part_type = None):
        GenericBrowser.__init__(self, a, store)
        self._assignment = assignment
        self._part_type = part_type

    def _header(self):
        w = urwid.Columns([
            ("fixed", 10, urwid.Text(u"datum")),
            urwid.Text(u"zdroj"),
            ("fixed", 15, urwid.Text(u"cena")),
            ("fixed", 6, urwid.Text(u"počet"))
            ], 3)
        return w

    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "body", "editfc_f")
        w = p(urwid.Columns([
            ("fixed", 10, urwid.Text(unicode(s.date))),
            urwid.Text(s.source.name),
            ("fixed", 15, urwid.Text(unicode(s.price))),
            ("fixed", 6, urwid.Text(unicode(s.count)))
            ], 3))
        w = app.Selectable(w)
        w._data = s
        return w

    @property
    def conditions(self):
        conds = [model.Or(self.MODEL.assignment == self._assignment, self.MODEL.assignment == None)]
        if self._assignment:
            conds.append(self.MODEL.part_type == self._assignment.part_type)
        if self._part_type:
            conds.append(self.MODEL.part_type == self._part_type)

        return conds

    def select(self, widget, id):
        return HistoryBrowser(self.app, self.store, history = widget._data.history)


class Browser(GenericBrowser):
    MODEL = model.PartType

    def _header(self):
        w = urwid.Columns([
            ("fixed", 15, urwid.Text(u"název")),
            urwid.Text(u"shrnutí"),
            urwid.Text(u"výrobce"),
            ("fixed", 6, urwid.Text(u"pinů")),
            ("fixed", 10, urwid.Text(u"pouzdro")),
            ("fixed", 6, urwid.Text(u"počet"))
            ], 2)
        return w

    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "body", "editfc_f")
        w = p(urwid.Columns([
            ("fixed", 15, urwid.Text(unicode(s.name))),
            urwid.Text(s.summary),
            urwid.Text(s.manufacturer),
            ("fixed", 6, urwid.Text(unicode(s.footprint.pins))),
            ("fixed", 10, urwid.Text(unicode(s.footprint.name))),
            ("fixed", 6, urwid.Text(unicode(s.parts.find(assignment=None).sum(model.Part.count)))),
            ], 2))
        w = app.Selectable(w)
        w._data = s
        return w

    def select(self, widget, id):
        return PartBrowser(self.app, self.store, assignment = None, part_type = widget._data)
