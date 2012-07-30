# encoding: utf8

import urwid
import app
import model

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class PartCreator(app.UIScreen):
    def __init__(self, a, store, partlist, back = None):
        app.UIScreen.__init__(self, a, store, back)
        self._partlist = partlist

    def show(self, args = None):
        # run all model pre-check verifiers
        errors = self.verify()
        if errors:
            self.back(errors[0])
        else:
            try:
                self.save()
                self.close()
            except Exception:
                self.back(0)

    def verify(self):
        return None

    def save(self):
        try:
            # save all data to db - completeness checking is done in model
            # verification methods
            for part in self._partlist:
                if not part.part_type:
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
                    new_part_type.manufacturer = part.manufacturer
                    self.store.add(new_part_type)
                    part.part_type = new_part_type

                # known part, just add new amount of it
                if int(part.count) > 0:
                    new_history = model.History()
                    new_history.event = model.History.INCOMING
                    self.store.add(new_history)

                    new_part = model.Part()
                    new_part.part_type = part.part_type
                    new_part.count = int(part.count)
                    new_part.date = part.date
                    new_part.price = float(part.unitprice)
                    new_part.source = part.source
                    new_part.history = new_history
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


class PartSelector(app.UIScreen):
    def __init__(self, a, store, partlist, action, action_kwargs = {}, back = None, create_new = True):
        app.UIScreen.__init__(self, a, store, back)
        self._partlist = [model.fill_matches(self.store, w) for w in partlist]
        self._save = app.SaveRegistry()
        self._spacer = urwid.Divider(u"-")
        self._current = 0
        self._create_new = create_new
        self._action = action
        self._action_kwargs = action_kwargs

    def _match_entry(self, selected_part_type, p_id):
        p = self.store.get(model.PartType, p_id)

        a = lambda w: urwid.AttrWrap(w, "editbx", "editfc")
        h = lambda w: urwid.AttrMap(w, {"header": "part header"}, {"header": "part header focus", "editbx": "editbx_f", "editfc": "editfc_f"})


        self.app.debug()

        sources = [urwid.Text(u"Zdroje")]

        for s in p.sources:
            sources.append(urwid.Columns([
                ("fixed", len(s.source.name), urwid.Text(s.source.name)),
                ("fixed", 1, urwid.Text(u"/")),
                urwid.Text(s.sku),
                urwid.Text(unicode(s.price)),
                ], 3))

        header = urwid.AttrWrap(urwid.Columns([
            urwid.Text(p.name),
            ("fixed", 10, urwid.Text(u"footprint")),
            ("fixed", 10, a(urwid.Text(p.footprint.name)))
            ], 3), "header")
        line2 = urwid.Columns([
            ("fixed", 10, urwid.Text("Shrnutí")),
            a(urwid.Text(p.summary)),
            ("fixed", 10, urwid.Text(u"pinů")),
            ("fixed", 10, a(urwid.Text(unicode(p.pins))))
            ], 3)
        line3 = urwid.Columns([
            ("fixed", 10, urwid.Text(u"")),
            urwid.Text(u""),
            ("fixed", 10, urwid.Text(u"počet")),
            ("fixed", 10, a(urwid.Text(unicode(p.count))))
            ], 3)
        line4 = urwid.Columns([
            ("fixed", 10, urwid.Text("Datasheet")),
            a(urwid.Text(p.datasheet)),
            ("fixed", 10, urwid.Text(u"")),
            ("fixed", 10, urwid.Text(u""))
            ], 3)
        desc_title = urwid.Text(u"Popis")
        desc = a(urwid.Text(p.description))

        pile = h(urwid.Pile([
            header,
            line2,
            line3,
            line4,
            urwid.Pile(sources),
            desc_title,
            desc,
            self._spacer
            ]))

        pile = app.Selectable(pile)

        pile._data = p
        return pile

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
        pile._data = None
        return pile

    def _notfound(self, part):
        return urwid.Text(u"Not found")

    def show(self, args = None):
        if args is None:
            args = 0

        self._current = args

        self._save.clear()
        part = self._partlist[args]
        listbox_content = []
        if self._create_new:
            listbox_content.append(self._entry(part))
        existing_parts = [self._match_entry(part.part_type, p) for p in part.matches]
        if existing_parts:
            listbox_content.extend(existing_parts)
        else:
            listbox_content.append(self._notfound(part))

        buttons = []
        if args > 0:
            buttons.append(urwid.Button(u"Předchozí", self.prev))
        else:
            buttons.append(urwid.Button(u"Zpět", lambda s,a: self.back))

        if args < len(self._partlist) - 1:
            buttons.append(urwid.Button(u"Další", self.next))
        else:
            buttons.append(urwid.Button(u"Uložit", self.save))

        listbox_content.append(urwid.Columns(buttons, 3))

        self.walker = urwid.SimpleListWalker(listbox_content)
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def next(self, signal, args = None):
        self.app.switch_screen(self, self._current + 1)

    def prev(self, signal, args = None):
        self.app.switch_screen(self, self._current - 1)

    def save(self, signal, args = None):
        for w in self._save:
            w.save()

        a = self.action(self.app, self.store, self._partslist, self, **self.action_kwargs)
        self.app.switch_screen(a)

class SearchForParts(app.UIScreen):
    def __init__(self, a, store, source = None, date = None, back = None, action = None, action_kwargs = {}, selector = PartSelector):
        app.UIScreen.__init__(self, a, store, back)
        self._date = None
        self._save = app.SaveRegistry()
        self._action = action
        self._action_kwargs = action_kwargs
        self._selector = selector

        self._source = source

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
            "part_type": None,
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

        w = self._selector(self.app, self.store, self.parts, back = self, action = self._action,
                           action_kwargs = self._action_kwargs)
        self.app.switch_screen(w)

    def input(self, key):
        if key == "f8":
            self.delete(self.walker, self.walker.get_focus())
        else:
            return key

    @property
    def parts(self):
        return [w._data for w in self.walker[1:-1]]
