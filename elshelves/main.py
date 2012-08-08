#!/usr/bin/python
# encoding: utf8

import urwid
import urwid.raw_display
import urwid.web_display
import model
import app
import sys

from part_selector import SearchForParts, PartSelector, PartCreator
from selector import GenericSelector, GenericEditor
from project_selector import ProjectSelector
from browser import Browser
from app import Edit, IntEdit, CheckBox, Button

class Actions(app.UIScreen):
    def show(self, args=None):
        content = [
            Button(_(u"Add parts"), self._switch_screen, SourceSelector),
            Button(_(u"Use parts"), self._switch_screen, ProjectSelector),
            Button(_(u"Browse parts"), self._switch_screen, Browser)
            ]

        self.body = urwid.GridFlow(content, 20, 3, 1, "left")
        return urwid.Filler(self.body)

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
        (_(u"Description: "), "description", Edit, {"multiline": True}, u""),
        ]

    def __init__(self, a, store, source=None, caller = None):
        if source is None:
            source = model.Source(
                name=u"",
                summary=u"",
                description=u"",
                home=u"http://",
                url=u"http://.../%s"
                )

        GenericEditor.__init__(self, a, store, source, caller)


class SourceSelector(GenericSelector):
    MODEL = model.Source
    EDITOR = SourceEditor

    def __init__(self, a, store):
        app.UIScreen.__init__(self, a, store)

    def select(self, widget, id):
        return SearchForParts(self.app, self.store,
                              back=self, action=PartCreator, source=widget._data)


def main():
    errlog = file("error_log", "w")
    model.debug(errlog)

    store = model.getStore("sqlite:shelves.sqlite3")
    text_header = "Shelves 0.0.0"
    a = app.App(text_header)
    actions_screen = Actions(a, store)
    a.switch_screen_modal(actions_screen)

if '__main__' == __name__ or urwid.web_display.is_web_request():
    main()
