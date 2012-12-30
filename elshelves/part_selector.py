# encoding: utf8

import urwid
import app
import model
from app import Edit, FloatEdit, IntEdit, CheckBox, Button


class PartCreator(app.UIScreen):
    def __init__(self, a, store, partlist, back=None):
        app.UIScreen.__init__(self, a, store, back)
        self._partlist = partlist

    def show(self, args=None):
        # run all model pre-check verifiers
        errors = self.verify()
        if errors:
            self.back(errors[0])
        else:
            try:
                self.save()
                self.close()
            except Exception, e:
                self.app.debug()
                self.back(0)

    def verify(self):
        errors = []
        for id,part in enumerate(self._partlist):
            if part.part_type:
                continue

            if not part.name:
                errors.append((id, _(u"Part name is missing")))

            if not part.footprint:
                errors.append((id, _(u"Part footprint is missing")))

            if not part.pins or part.pins == u"0":
                errors.append((id, _(u"Part must have more than 0 pins")))

        return errors

    @staticmethod
    def create_part_type(store, part):
        # get or create footprint
        footprint = store.find(model.Footprint,
                                    name=part.footprint).one()
        if footprint is None:
            footprint = model.Footprint()
            footprint.name = part.footprint
            footprint.pins = int(part.pins)
            store.add(footprint)

        # part_type
        new_part_type = model.PartType()
        new_part_type.footprint = footprint
        new_part_type.name = part.name
        new_part_type.summary = part.summary
        new_part_type.description = part.description
        new_part_type.datasheet = part.datasheet
        new_part_type.pins = int(part.pins)
        new_part_type.manufacturer = part.manufacturer
        store.add(new_part_type)

        # update records in search term table
        model.Term.register(new_part_type)

        return new_part_type

    def save(self):
        try:
            # save all data to db - completeness checking is done in model
            # verification methods
            new_history = model.History()
            new_history.event = model.History.INCOMING
            self.store.add(new_history)

            for part in self._partlist:
                if not part.part_type:
                    # unknown part create part type and all dependencies
                    part.part_type = PartCreator.create_part_type(self.store, part)

                # known part, just add new amount of it
                if part.source and int(part.count) > 0:
                    new_part = model.Part()
                    new_part.part_type = part.part_type
                    new_part.count = int(part.count)
                    if part.date:
                        new_part.date = part.date
                    if part.unitprice is not None:
                        new_part.price = float(part.unitprice)
                        if part.vat is not None:
                            new_part.vat = float(part.vat)
                    new_part.source = part.source
                    new_part.history = new_history
                    self.store.add(new_part)

                # check if we have ever bought it from this source (with this
                # sku if it was entered)
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
        except Exception:
            self.store.rollback()
            raise


class PartSelector(app.UIScreen):
    def __init__(self, a, store, partlist, action, action_kwargs={},
                 back=None, create_new=True):
        app.UIScreen.__init__(self, a, store, back)
        self._partlist = [model.fill_matches(self.store, w) for w in partlist]
        self._save = app.SaveRegistry()
        self._spacer = urwid.Divider(u" ")
        self._current = 0
        self._create_new = create_new
        self._action = action
        self._action_kwargs = action_kwargs

        self._h = lambda w: urwid.AttrMap(w,
                                          {},
                                          {"part": "part_f",
                                           "part_c": "part_fc",
                                           "edit": "edit_f",
                                           "edit_c": "edit_fc"})
        self._a = lambda w: urwid.AttrWrap(w, "edit")
        self._c = lambda w: urwid.AttrWrap(w, "edit_c")

    def _match_entry(self, selected_part_type, p_id):
        p = self.store.get(model.PartType, p_id)

        sources = [urwid.Text(_(u"Sources"))]

        for s in p.sources:
            sources.append(urwid.Columns([
                ("fixed", len(s.source.name), urwid.Text(s.source.name)),
                ("fixed", 1, urwid.Text(u"/")),
                urwid.Text(s.sku),
                urwid.Text(unicode(s.price)),
                ], 3))

        header = urwid.AttrWrap(urwid.Text(p.name), "part")
        line2 = urwid.Columns([
            ("fixed", 10, urwid.Text(_(u"summary"))),
            self._c(urwid.Text(p.summary)),
            ("fixed", 10, urwid.Text(_(u"pins"))),
            ("fixed", 10, self._c(urwid.Text(unicode(p.pins))))
            ], 3)
        line3 = urwid.Columns([
            ("fixed", 10, urwid.Text(_(u"footprint"))),
            self._c(urwid.Text(p.footprint.name)),
            ("fixed", 10, urwid.Text(_(u"count"))),
            ("fixed", 10, self._c(urwid.Text(unicode(p.count))))
            ], 3)
        line4 = urwid.Columns([
            ("fixed", 10, urwid.Text(_(u"manufacturer"))),
            self._c(urwid.Text(p.manufacturer)),
            ], 3)
        line5 = urwid.Columns([
            ("fixed", 10, urwid.Text(_(u"datasheet"))),
            self._c(urwid.Text(p.datasheet)),
            ], 3)
        desc_title = urwid.Text(_(u"description"))
        desc = self._c(urwid.Text(p.description))

        pile = urwid.Pile([
            header,
            line2,
            line3,
            line4,
            line5,
            urwid.Pile(sources),
            desc_title,
            desc,
            self._spacer
            ])

        pile = app.Selectable(pile)

        pile._data = p
        return pile

    def _entry(self, p):
        header = urwid.AttrWrap(urwid.Text(_(u"New part type")), "part")
        line1 = urwid.Columns([
            ("fixed", 12, urwid.Text(_(u"name"))),
            self._a(Edit(u"", p.name or p.search_name)
                    .bind(p, "name").reg(self._save)),
            ("fixed", 10, urwid.Text(_(u"footprint"))),
            ("fixed", 10, self._a(Edit(u"", p.footprint)
                                  .bind(p, "footprint").reg(self._save)))
            ], 1)
        line2 = urwid.Columns([
            ("fixed", 12, urwid.Text(_(u"summary"))),
            self._a(Edit(u"", p.summary).bind(p, "summary")
                    .reg(self._save)),
            ("fixed", 10, urwid.Text(_(u"pins"))),
            ("fixed", 10, self._a(IntEdit(u"", unicode(p.pins), align = "right")
                                  .bind(p, "pins").reg(self._save)))
            ], 1)

        line3_content = [
            ("fixed", 12, urwid.Text(_(u"manufacturer"))),
            self._a(Edit(u"", p.manufacturer).bind(p, "manufacturer")
                    .reg(self._save)) ]

        line3 = urwid.Columns(line3_content, 1)
        line4 = urwid.Columns([
            ("fixed", 12, urwid.Text(_(u"datasheet"))),
            self._a(Edit(u"", p.datasheet).bind(p, "datasheet")
                    .reg(self._save)),
            ], 1)
        desc_title = urwid.Text(_(u"description"))
        desc = self._a(Edit(u"", p.description, multiline=True)
                       .bind(p, "description").reg(self._save))

        pile = urwid.Pile([
            header,
            line1,
            line2,
            line3,
            line4,
            desc_title,
            desc,
            self._spacer
            ])
        pile._data = None
        return pile

    def _notfound(self, p):
        return urwid.Text(_(u"No part type found"))

    def _header(self, p):
        if p.date:
            date = unicode(p.date.strftime("%Y-%m-%d"))
        else:
            date = _(u"-today-")

        cols_1 = [
            ("fixed", 2*len("%d" % len(self._partlist))+3, urwid.Text(u"[%d/%d]" %
                                          (self._current + 1, len(self._partlist)))),

            ("fixed", len(date), urwid.Text(date)),
            ("weight", 1, urwid.Text(p.search_name)),
            ("fixed", 6, urwid.Text(_(u"count:"))),
            ("fixed", 5, self._a(IntEdit(u"", p.count, align = "right").bind(p, "count")
                                 .reg(self._save)))
            ]


        cols_2 = []

        if p.source:
            cols_2.extend([
                ("weight", 1, urwid.Text(p.source.name)),
                ("fixed", 4, urwid.Text(_(u"sku:"))),
                ("fixed", 10, self._a(Edit(u"", p.sku).bind(p, "sku")
                                      .reg(self._save))),
                ("fixed", 6, urwid.Text(_(u"price:"))),
                ("fixed", 6, self._a(FloatEdit(u"", p.unitprice, align = "right", allow_none = True).bind(p, "unitprice")
                                     .reg(self._save))),
                ("fixed", 4, urwid.Text(_(u"vat:"))),
                ("fixed", 5, self._a(FloatEdit(u"", p.vat, align = "right", allow_none = True).bind(p, "vat")
                                     .reg(self._save)))
                ])

        pile_content = [ urwid.Columns(cols_1, 1) ]
        if cols_2:
            pile_content.append(urwid.Columns(cols_2, 1))

        return [urwid.AttrWrap(urwid.Pile(pile_content), "part")]

    def show(self, args=None):
        if len(self._partlist) == 0:
            self.back()
            return

        if args is None or args >= len(self._partlist):
            args = 0

        self._current = args

        self._save.clear()
        part = self._partlist[args]
        listbox_content = []

        existing_parts = [self._match_entry(part.part_type, p)
                          for p in part.matches]
        if self._create_new:
            # fill number of pins based on previous input (either from footprint
            # db or from different part with the same footprint)
            if not part.pins and part.footprint:
                footprint = self.store.find(model.Footprint,
                                            model.Footprint.name
                                            .like(part.footprint, "$", False)).one()
                if footprint:
                    part.pins = footprint.pins
                else:
                    for p in self._partlist:
                        if part.part_type:
                            continue

                        if part.footprint.lower() == p.footprint.lower() and p.pins:
                            part.pins = p.pins

            existing_parts.append(self._entry(part))

        if part.part_type and not part.part_type.id in part.matches:
            part.part_type = None

        if part.part_type is None and len(existing_parts) == 1:
            part.part_type = existing_parts[0]._data

        #sort the content so the selected part is on top
        head_part = filter(lambda p: p._data == part.part_type, existing_parts)
        if head_part:
            pile = self._h(urwid.Pile(
                self._header(part) +
                [
                head_part[0]
                ]))
            pile._data = head_part[0]._data
            listbox_content.append(pile)
        else:
            listbox_content.append(self._notfound(part))

        buttons = []
        if args > 0:
            buttons.append(Button(_(u"Previous"), self.prev))
        else:
            buttons.append(Button(_(u"Back"), lambda a: self.back()))

        if part.part_type and self._create_new:
            buttons.append(Button(_(u"Modify"), self.modify))

        if args < len(self._partlist) - 1:
            buttons.append(Button(_(u"Next"), self.next))
        else:
            buttons.append(Button(_(u"Save"), self.save))

        listbox_content.append(urwid.Columns(buttons, 3))

        buttons = []
        buttons.append(Button(_(u"Remove"), self.remove))

        listbox_content.append(urwid.Columns(buttons, 3))

        if len(existing_parts) > 1:
            def _hdata(p):
                h = self._h(p)
                h._data = p._data
                return h
            listbox_content.extend([self._spacer, urwid.Text(_(u"Other possible part types:")), urwid.Divider(u"="), self._spacer])
            listbox_content.extend([_hdata(p) for p in existing_parts if p._data != part.part_type])

        self.walker = urwid.SimpleListWalker(listbox_content)
        self.body = urwid.ListBox(self.walker)

        return self.body

    def next(self, signal, args=None):
        for w in self._save:
            w.save()

        self.app.switch_screen(self, self._current + 1)

    def remove(self, signal, args=None):
        del self._partlist[self._current]
        self.app.switch_screen(self, self._current)

    def prev(self, signal, args=None):
        for w in self._save:
            w.save()

        self.app.switch_screen(self, self._current - 1)

    def save(self, signal, args=None):
        for w in self._save:
            w.save()

        a = self._action(self.app, self.store, self._partlist, back = self, **self._action_kwargs)
        self.app.switch_screen(a)

    def modify(self, signal, args=None):
        self._partlist[self._current].load(self._partlist[self._current].part_type)
        self._partlist[self._current].part_type = None
        self.app.switch_screen(self, self._current)

    def input(self, key):
        if key == "enter":
            for w in self._save:
                w.save()

            w, id = self.walker.get_focus()
            self._partlist[self._current].part_type = w._data
            self.app.switch_screen(self, self._current)
            return None
        else:
            return key

    @property
    def footer(self):
        """Method called after show, returns new window footer."""
        return u""

    @property
    def title(self):
        """Method called after show, returns new window title."""
        s = u"Select the part to use"
        if self._create_new:
            s += " or create new one"
        return s


class SearchForParts(app.UIScreen):
    CONFIRM_CLOSE = "Do you really want to close this screen? You will loose all the data you have entered."

    def __init__(self, a, store, back=None, action=None,
                 action_kwargs={}, selector=PartSelector, parts = [], extra=None):
        app.UIScreen.__init__(self, a, store, back)
        self._save = app.SaveRegistry()
        self._action = action
        self._action_kwargs = action_kwargs
        self._selector = selector
        self._extra = extra

        w = urwid.Columns([
            ("weight", 2, urwid.Text(_(u"name"))),
            ("fixed", 10, urwid.Text(_(u"footprint"))),
            ("fixed", 12, urwid.Text(_(u"manufacturer"))),
            ("fixed", 10, urwid.Text(_(u"sku"))),
            ("fixed", 6, urwid.Text(_(u"count"))),
            ("fixed", 6, urwid.Text(_(u"price"))),
            ], 1)

        buttons = urwid.Columns([
            ("fixed", 16, Button(_(u"Add line"), self.add)),
            ("fixed", 25, Button(_(u"Save and search"), self.save)),
            urwid.Divider(u" ")
            ], 3)

        content = [w]
        content.extend([self._entry(p) for p in parts])
        content.append(buttons)

        self.walker = urwid.SimpleListWalker(content)


    def _entry(self, s):
        p = lambda w: urwid.AttrWrap(w, "edit", "edit_f")
        w = urwid.Columns([
            ("weight", 2, p(Edit(u"", s.search_name).bind(s, "search_name").reg(self._save))),
            ("fixed", 10, p(Edit(u"", s.footprint).bind(s, "footprint").reg(self._save))),
            ("fixed", 12, p(Edit(u"", s.manufacturer).bind(s, "manufacturer").reg(self._save))),
            ("fixed", 10, p(Edit(u"", s.sku).bind(s, "sku").reg(self._save))),
            ("fixed", 6, p(IntEdit(u"", unicode(s.count), align = "right").bind(s, "count").reg(self._save))),
            ("fixed", 6, p(FloatEdit(u"", unicode(s.unitprice)).bind(s, "unitprice").reg(self._save))),
            ], 1)
        w._data = s
        return w

    def show(self, args=None):
        listbox = urwid.ListBox(self.walker)
        self.body = urwid.AttrWrap(listbox, 'body')

        return self.body

    def add(self, signal, args=None):
        p = model.RawPart(self._extra)

        buttons = self.walker.pop()
        self.walker.append(self._entry(p))
        self.walker.append(buttons)
        self.walker.set_focus(len(self.walker) - 2)

    def delete(self, list, focus):
        widget, id = focus
        if id != 0 and id < len(list) - 1:
            del list[id]

    def save(self, signal, args=None):
        # save all values from widgets to storage
        for w in self._save:
            w.save()

        w = self._selector(self.app, self.store, self.parts,
                           back=self, action=self._action,
                           action_kwargs=self._action_kwargs)
        self.app.switch_screen(w)

    def input(self, key):
        if key == "f8":
            self.delete(self.walker, self.walker.get_focus())
        else:
            return app.UIScreen.input(self, key)

    @property
    def parts(self):
        return [w._data for w in self.walker[1:-1]]

    @property
    def title(self):
        return _(u"Search for parts")

    @property
    def footer(self):
        return _(u"Fill search data and press <Save and search>, F8 deletes line.")
