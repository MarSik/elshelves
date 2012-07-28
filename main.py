#!/usr/bin/python
# encoding: utf8

__version__ = "0.0.0"
__author__ = "Martin Sivak <mars@montik.net>"

import urwid
import urwid.raw_display
import urwid.web_display
import model
import app

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

def e(w):
    return urwid.AttrWrap(w, "editbx", "editfc")

class PartEditor(app.UIScreen):
    def __init__(self, a, store, partlist = None, back = None):
        app.UIScreen.__init__(self, a, store, back)
        self._partlist = partlist
        self._save = app.SaveRegistry()
        self._spacer = urwid.Divider(u"-")

    def _entry(self, p):
        a = lambda w: urwid.AttrWrap(w, "editbx", "editfc")
        h = lambda w: urwid.AttrMap(w, {"header": "part header"}, {"header": "part header focus", "editbx": "editbx_f", "editfc": "editfc_f"})
        header = urwid.AttrWrap(urwid.Columns([
            ("weight", 2, urwid.Text(p.search_name)),
            urwid.Text(p.date or u"-dnes-"),
            ("fixed", len(p.source.name), urwid.Text(p.source.name)),
            ("fixed", 1, urwid.Text(u"/")),
            a(urwid.Edit(u"", p.sku).bind(p, "sku").reg(self._save)),
            ("weight", 1, urwid.Text(u"F:%d" % len(p.matches)))
            ], 1), "header")
        line1 = urwid.Columns([
            ("fixed", 10, urwid.Text("Název")),
            a(urwid.Edit(u"", p.name).bind(p, "name").reg(self._save)),
            ("fixed", 10, urwid.Text(u"footprint")),
            ("fixed", 10, a(urwid.Edit(u"", p.footprint).bind(p, "footprint").reg(self._save)))
            ], 3)
        line2 = urwid.Columns([
            ("fixed", 10, urwid.Text("Shrnutí")),
            a(urwid.Edit(u"", p.summary).bind(p, "summary").reg(self._save)),
            ("fixed", 10, urwid.Text(u"pinů")),
            ("fixed", 10, a(urwid.IntEdit(u"", unicode(p.pins)).bind(p, "pins").reg(self._save)))
            ], 3)
        line3 = urwid.Columns([
            ("fixed", 10, urwid.Text("Výrobce")),
            a(urwid.Edit(u"", p.manufacturer).bind(p, "manufacturer").reg(self._save)),
            ("fixed", 10, urwid.Text(u"počet")),
            ("fixed", 10, a(urwid.IntEdit(u"", unicode(p.count)).bind(p, "count").reg(self._save)))
            ], 3)
        line4 = urwid.Columns([
            ("fixed", 10, urwid.Text("Datasheet")),
            a(urwid.Edit(u"", p.datasheet).bind(p, "datasheet").reg(self._save)),
            ("fixed", 10, urwid.Text(u"cena")),
            ("fixed", 10, a(urwid.Edit(u"", unicode(p.unitprice)).bind(p, "unitprice").reg(self._save)))
            ], 3)
        desc_title = urwid.Text(u"Popis")
        desc = a(urwid.Edit(u"", p.description, multiline = True).bind(p, "description").reg(self._save))

        pile = h(urwid.Pile([
            header,
            line1,
            line2,
            line3,
            line4,
            desc_title,
            desc,
            self._spacer
            ]))
        pile._data = p
        return pile

    def show(self, args = None):
        self._save.clear()
        listbox_content = [self._entry(p) for p in self._partlist]
        listbox_content.append(urwid.Button(u"Save", self.save))
        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def save(self, signal, args = None):
        # save all widgets to data objects
        for w in self._save:
            w.save()

        try:
            # save all data to db - completeness checking is done in model
            # verification methods
            for part in self._partlist:
                if not part.part_type_id:
                    # unknown part create part type and all dependencies
                    
                    # get or create footprint
                    footprint = self.store.find(model.Footprint, name = part.footprint).one()
                    if footprint is None:
                        footprint = model.Footprint()
                        footprint.name = part.footprint
                        footprint.pins = part.pins
                        self.store.add(footprint)

                    # part_type
                    new_part_type = model.PartType()
                    new_part_type.footprint = footprint
                    new_part_type.name = part.name
                    new_part_type.summary = part.summary
                    new_part_type.description = part.description
                    new_part_type.datasheet = part.datasheet
                    new_part_type.pins = int(part.pins)
                    self.store.add(new_part_type)
                    
                    part.part_type_id = new_part_type.id
                    part.part_type = new_part_type
                else:
                    part.part_type = self.store.get(model.PartType, part.part_type_id)
                    
                # known part, just add new amount of it
                if int(part.count) > 0:
                    new_part = model.Part()
                    new_part.part_type = part.part_type
                    new_part.count = int(part.count)
                    new_part.date = part.date
                    new_part.price = float(part.unitprice)
                    new_part.manufacturer = part.manufacturer
                    new_part.source = part.source
                    self.store.add(new_part)

                # check if we have ever bought it from this source (with this sku if it was entered)
                sources = part.part_type.sources.find(model.PartSource.source == part.source)
                if part.sku:
                    sources = filter(lambda s: s.sku == part.sku, sources)

                # if not and sku was entered, create new sku
                if not sources and part.sku:
                    # source/sku record
                    source = model.PartSource()
                    source.part_type = part.part_type
                    source.source = part.source
                    source.sku = part.sku
                    self.store.add(source)

            self.store.commit()
            self.close()
        except Exception:
            self.store.rollback()
            raise

class NewPartList(app.UIScreen):
    def __init__(self, a, store, source, date = None, back = None):
        app.UIScreen.__init__(self, a, store, back)
        self._source = source
        self._date = None
        self._save = app.SaveRegistry()

        w = urwid.Columns([
            ("weight", 2, urwid.Text(u"name")),
            ("fixed", 10, urwid.Text(u"footprint")),
            ("weight", 1, urwid.Text(u"manufacturer")),
            ("fixed", 10, urwid.Text(u"sku")),
            ("fixed", 6, urwid.Text(u"count")),
            ("fixed", 6, urwid.Text(u"$$")),
            ], 3)

        buttons = urwid.Columns([
            ("fixed", 16, urwid.Button(u"Přidat řádek", self.add)),
            ("fixed", 16, urwid.Button(u"Další krok", self.save)),
            urwid.Divider(u" ")
            ], 3)


        self.walker = urwid.SimpleListWalker([w, buttons])

    def _newpart(self):
        p = {
            "part_type_id": u"",
            "search_name": u"",
            "name": u"",
            "summary": u"",
            "description": u"",
            "footprint": u"",
            "pins": 0,
            "manufacturer": u"",
            "sku": u"",
            "count": 0,
            "date": self._date,
            "unitprice": 0,
            "source": self._source,
            "datasheet": u"",
            "matches": []
            }

        return Struct(**p)

    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "editbx_f", "editfc_f")
        w = urwid.Columns([
            ("weight", 2, p(urwid.Edit(u"", s.search_name).bind(s, "search_name").reg(self._save))),
            ("fixed", 10, p(urwid.Edit(u"", s.footprint).bind(s, "footprint").reg(self._save))),
            ("weight", 1, p(urwid.Edit(u"", s.manufacturer).bind(s, "manufacturer").reg(self._save))),
            ("fixed", 10, p(urwid.Edit(u"", s.sku).bind(s, "sku").reg(self._save))),
            ("fixed", 6, p(urwid.IntEdit(u"", unicode(s.count)).bind(s, "count").reg(self._save))),
            ("fixed", 6, p(urwid.Edit(u"", unicode(s.unitprice)).bind(s, "unitprice").reg(self._save))),
            ], 3)
        w._data = s
        return w

    def show(self, args = None):
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def add(self, signal, args = None):
        p = self._newpart()

        buttons = self.walker.pop()
        self.walker.append(self._entry(p))
        self.walker.append(buttons)
        self.walker.set_focus(len(self.walker) - 2)

    def delete(self, list, focus):
        widget, id = focus
        if id != 0 and id < len(list) - 1:
            del list[id]

    def save(self, signal, args = None):
        # save all values from widgets to storage
        for w in self._save:
            w.save()

        w = PartEditor(self.app, self.store, self.parts, self)
        self.app.switch_screen(w)

    def input(self, key):
        if key == "f8":
            self.delete(self.walker, self.walker.get_focus())
        else:
            return key

    @property
    def parts(self):
        return [model.fill_matches(self.store, w._data) for w in self.walker[1:-1]]

class SourceSelector(app.UIScreen):
    def __init__(self, a, store):
        app.UIScreen.__init__(self, a, store)

    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "body", "editfc_f")
        w = p(urwid.Columns([
            ("fixed", 15, urwid.Text(unicode(s.name))),
            urwid.Text(unicode(s.summary)),
            ], 3))
        w = app.Selectable(w)
        w._data = s
        return w

    def show(self, args = None):
        listbox_content = [self._entry(s) for s in self.store.find(model.Source)]
        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def input(self, key):
        if key == "n":
            new_source = SourceEditor(self.app, self.store)
            self.app.switch_screen_with_return(new_source)
        elif key == "e":
            widget, id = self.walker.get_focus()
            source = SourceEditor(self.app, self.store, widget._data)
            self.app.switch_screen_with_return(source)
        elif key == "enter":
            widget, id = self.walker.get_focus()
            w = NewPartList(self.app, self.store, widget._data)
            self.app.switch_screen_with_return(w)
        else:
            return key

class SourceEditor(app.UIScreen):
    def __init__(self, a, store, source = None):
        app.UIScreen.__init__(self, a, store)
        if source is None:
            source = model.Source(
                name = u"",
                summary = u"",
                description = u"",
                home = u"http://",
                url = u"http://.../%s"
                )
        self._source = source
        self._save = app.SaveRegistry()

    def show(self, args = None):
        self._save.clear()
        listbox_content = [
            urwid.Edit(u"Název", self._source.name or u"").bind(self._source, "name").reg(self._save),
            urwid.Edit(u"Homepage", self._source.home or u"").bind(self._source, "home").reg(self._save),
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

def main():
    store = model.getStore("sqlite:shelves.sqlite3")
    text_header = "Shelves 0.0.0"
    a = app.App(text_header)

    source_screen = SourceSelector(a, store)
    a.switch_screen_modal(source_screen)

if '__main__'==__name__ or urwid.web_display.is_web_request():
    main()
