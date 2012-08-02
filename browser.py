# encoding: utf8

import app
import model
import urwid
from selector import GenericSelector

class PartBrowser(GenericSelector):
    MODEL = model.Part
    EDITOR = None

    def __init__(self, a, store, assignment = None, part_type = None):
        GenericSelector.__init__(self, a, store)
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

    def add(self):
        pass

    def edit(self, widget, id):
        return None

    def select(self, widget, id):
        # todo select the part pile to get parts from
        pass


class Browser(GenericSelector):
    MODEL = model.PartType
    EDITOR = None

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


    def add(self):
        pass

    def edit(self, widget, id):
        pass

    def remove(self, widget, id):
        pass

    def select(self, widget, id):
        return PartBrowser(self.app, self.store, assignment = None, part_type = widget._data)
