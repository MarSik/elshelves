#!/usr/bin/python
# encoding: utf8

__version__ = "0.0.0"
__author__ = "Martin Sivak <mars@montik.net>"

import urwid
import urwid.raw_display
import urwid.web_display
import model
import app
import sys

from part_selector import SearchForParts, PartSelector, PartCreator
from selector import GenericSelector, GenericEditor
from project_selector import ProjectSelector


def e(w):
    return urwid.AttrWrap(w, "editbx", "editfc")


class Actions(app.UIScreen):
    def show(self, args=None):
        content = [
            urwid.Button(u"Příjem", self._switch_screen, SourceSelector),
            urwid.Button(u"Projekt", self._switch_screen, ProjectSelector)
            ]

        self.body = urwid.GridFlow(content, 13, 3, 1, "left")
        return urwid.Filler(self.body)

    def _switch_screen(self, signal, screen):
        s = screen(self.app, self.store)
        self.app.switch_screen_with_return(s)


class SourceEditor(GenericEditor):
    MODEL = model.Source

    def __init__(self, a, store, source=None):
        if source is None:
            source = model.Source(
                name=u"",
                summary=u"",
                description=u"",
                home=u"http://",
                url=u"http://.../%s"
                )

        GenericEditor.__init__(self, a, store, source)

    def show(self, args=None):
        self._save.clear()
        listbox_content = [
            urwid.Edit(u"Název", self._item.name or u"")
                 .bind(self._item, "name").reg(self._save),
            urwid.Edit(u"Homepage", self._item.home or u"")
                 .bind(self._item, "home").reg(self._save),
            urwid.Edit(u"Krátký popis", self._item.summary or u"")
                 .bind(self._item, "summary").reg(self._save),
            urwid.Text(u"Popis"),
            urwid.Edit(u"", self._item.description or u"", multiline=True)
                 .bind(self._item, "description").reg(self._save),
            urwid.Divider(u" "),
            urwid.Button(u"Uložit", self.save)
            ]
        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body


class SourceSelector(GenericSelector):
    MODEL = model.Source
    EDITOR = SourceEditor

    def __init__(self, a, store):
        app.UIScreen.__init__(self, a, store)

    def select(self, widget, id):
        return SearchForParts(self.app, self.store,
                              action=PartCreator, source=widget._data)


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
