#!/usr/bin/python
# encoding: utf8

import urwid
import model
import app
import sys

from part_selector import SearchForParts, PartSelector, PartCreator
from generics import GenericSelector, GenericEditor
from project_selector import ProjectSelector
from browser import Browser, FootprintBrowser, RawPartBrowser
from app import Edit, FloatEdit, IntEdit, CheckBox, Button
from amountdlg import DateDialog
import datetime

class SearchBrowser(Browser):
    SEARCH_FIELDS = Browser.SEARCH_FIELDS + ["manufacturer"]

    def __init__(self, app_inst, store, search):
        Browser.__init__(self, app_inst, store, search = search)
        self._save = app.SaveRegistry()
        self.search_field = app.Edit(u"", search).bind(self, "search")
        urwid.connect_signal(self.search_field, "enter", self.do_search)

    def header(self, args = None):
        return [urwid.AttrWrap(self.search_field.reg(self._save), "edit", "edit_f"), urwid.Divider(" ")] + Browser.header(self)

    @property
    def conditions(self):
        conds = []

        if self.search:
            search_terms = [self.MODEL.id == part_type.id
                            for part_type in model.Term.search(self.store, self.search)]
            if search_terms:
                conds.append(model.Or(search_terms))
            else:
                conds.append(False)

        return conds

    def do_search(self, widget = None):
        for w in self._save:
            w.save()

        self.app.switch_screen(self)

class Actions(app.UIScreen):
    def __init__(self, app_inst, store):
        app.UIScreen.__init__(self, app_inst, store)
        self._save = app.SaveRegistry()
        self._search = u""

    def show(self, args=None):
        self._save.clear()
        self.search_field = app.Edit(u"", u"").bind(self, "_search").reg(self._save)
        urwid.connect_signal(self.search_field, "enter", self.search)

        content = [
            Button(_(u"Add parts"), self._switch_screen, SourceSelector),
            Button(_(u"Use parts"), self._switch_screen, ProjectSelector),
            Button(_(u"Browse parts"), self._switch_screen, Browser),
            Button(_(u"Browse footprints"), self._switch_screen, FootprintBrowser),
            Button(_(u"Browse raw"), self._switch_screen, RawPartBrowser)
            ]

        self.body = urwid.Filler(urwid.Pile([
            urwid.GridFlow(content, 16, 3, 1, "left"),
            urwid.Divider(u" "),
            urwid.Columns([
                ("fixed", 13, urwid.Text(_(u"Search parts:"))),
                urwid.AttrWrap(self.search_field, "edit", "edit_f")
                ], 1)
            ]))

        return urwid.Padding(self.body, width = 54, align = "center")

    def search(self, widget = None):
        for w in self._save:
            w.save()

        search = SearchBrowser(self.app, self.store, search = self._search)
        self.app.switch_screen_with_return(search)
        return True

    def _switch_screen(self, signal, screen):
        s = screen(self.app, self.store)
        self.app.switch_screen_with_return(s)

    @property
    def footer(self):
        return _(u"Press ESC to exit")

class SourceEditor(GenericEditor):
    MODEL = model.Source
    FIELDS = [
        (_(u"Name: "), "name", Edit, {}, u""),
        (_(u"Homepage: "), "home", Edit, {}, u""),
        (_(u"Summary: "), "summary", Edit, {}, u""),
        (_(u"Vat: "), "vat", FloatEdit, {"allow_none": True}, u""),
        (_(u"Description: "), "description", Edit, {"multiline": True}, u""),
        ]

    def __init__(self, a, store, item=None, caller = None):
        if item is None:
            item = model.Source(
                name=u"",
                summary=u"",
                description=u"",
                home=u"http://",
                url=u"http://.../%s"
                )

        GenericEditor.__init__(self, a, store, item, caller)


class SourceSelector(GenericSelector):
    MODEL = model.Source
    EDITOR = SourceEditor

    def __init__(self, a, store):
        GenericSelector.__init__(self, a, store)

    def select(self, widget, id):
        dialog = DateDialog(self.app, _(u"Date"), _(u"When did you get the new parts?"),
                            datetime.date.today())
        ok = self.app.run_dialog(dialog)
        if not ok:
            return

        return SearchForParts(self.app, self.store,
                              back=self, action=PartCreator,
                              extra = {
                                  "date": dialog.value,
                                  "source": widget._data,
                                  "vat": widget._data.vat})

    @property
    def title(self):
        return _(u"Select a source (vendor) for incoming parts")
