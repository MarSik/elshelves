# encoding: utf8

import app
import urwid
import model
from generics import GenericSelector, GenericEditor
from part_selector import SearchForParts, PartCreator
from browser import PartBrowser
from app import Edit, IntEdit, CheckBox, Button
from amountdlg import AmountDialog

class AssignmentPartSelector(PartBrowser):
    KEYS = PartBrowser.KEYS + {
        "h": (_(u"history"), "history", PartBrowser.ALWAYS),
        "S": (_(u"solder"), "solder", PartBrowser.ALWAYS),
        "D": (_(u"desolder"), "desolder", PartBrowser.ALWAYS),
        "K": (_(u"kill"), "kill", PartBrowser.ALWAYS)
        }

    def do_solder(self, pile, msg, solder = True):
        if not self._assignment or pile.assignment != self._assignment:
            return

        if pile.count > 1:
            amdlg = AmountDialog(self.app, _(u"%s [%s]") % (pile.part_type.name, pile.part_type.footprint.name),
                                 _(u"How many parts were %s [max %d] ?" % (msg, pile.count)),
                                 pile.count)

            if self.app.run_dialog(amdlg):
                pile = pile.take(amdlg.value)
                self.store.add(pile)
            else:
                pile = None

        if pile:
            pile.soldered = solder
            self.store.commit()
            return self.REFRESH

    def solder(self, widget, id):
        return self.do_solder(widget._data, _(u"soldered"), solder = True)

    def desolder(self, widget, id):
        return self.do_solder(widget._data, _(u"unsoldered"), solder = False)

    def kill(self, widget, id):
        amdlg = AmountDialog(self.app, _(u"%s [%s]") % (widget._data.part_type.name, widget._data.part_type.footprint.name),
                             _(u"How many parts were destroyed [max %d] ?" % widget._data.count),
                             0)

        if self.app.run_dialog(amdlg):
            pile = widget._data.take(amdlg.value)
            pile.assignment = None
            pile.usable = False
            self.store.add(pile)
            self.store.commit()
            return self.REFRESH

    # enter should allow changing the amount and we need to remap the history screen
    history = PartBrowser.select

    def select(self, widget, id):
        if self._assignment == widget._data.assignment:
            used = widget._data.count
        else:
            used = 0

        amdlg = AmountDialog(self.app, _(u"%s [%s]") % (widget._data.part_type.name, widget._data.part_type.footprint.name),
                             _(u"Maximum number of parts to take from this pile [max %d] ?" % widget._data.count),
                             widget._data.count)

        if not self.app.run_dialog(amdlg):
            return

        # unused pile, take parts from it
        if used == 0 and amdlg.value > 0:
            self._assignment.assign(widget._data, maximum = amdlg.value)
            self.store.commit()

        # used pile, remove parts from it
        elif used > 0 and amdlg.value < used:
            pile = widget._data.take(used - amdlg.value)
            pile.assignment = None
            self.store.add(pile)
            self.store.commit()

        return self.REFRESH


class ItemAssigner(app.UIScreen):
    def __init__(self, a, store, partlist, item, back=None):
        app.UIScreen.__init__(self, a, store, back)
        self._item = item
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
                self.back(0)

    def verify(self):
        return None

    def save(self):
        try:
            # save all data to db - completeness checking is done in model
            # verification methods
            for part in self._partlist:
                if not part.part_type:
                    part.part_type = PartCreator.create_part_type(self.store, part)

                assert part.part_type is not None

                # known part, just assign new amount request of it
                if int(part.count) > 0:
                    new_part = model.Assignment()
                    new_part.part_type = part.part_type
                    new_part.item = self._item
                    new_part.count = int(part.count)
                    self.store.add(new_part)

                    # if there is only one unused pile of parts, assign it
                    piles = self.store.find(model.Part, part_type=part.part_type, assignment=None)
                    if piles:
                        piles = list(piles)
                    else:
                        piles = []

                    if len(piles) == 1:
                        new_part.assign(piles[0])

            self.store.commit()
        except Exception, e:
            self.app.debug()
            self.store.rollback()


class AssignmentSelector(GenericSelector):
    MODEL = model.Assignment
    EDITOR = True
    FIELDS = [
        (_(u"type"), "fixed", 15, "part_type.name"),
        (_(u"footprint"), "fixed", 10, "part_type.footprint.name"),
        (_(u"summary"), "weight", 1, "part_type.summary"),
        (_(u"manufacturer"), "fixed", 15, "part_type.manufacturer"),
        (_(u"req"), "fixed", 3, "count"),
        (_(u"cnt"), "fixed", 3, "count_assigned"),
        (_(u"sld"), "fixed", 3, "count_soldered"),
        ]

    def __init__(self, a, store, item):
        GenericSelector.__init__(self, a, store)
        self._item = item
        self._amdlg = AmountDialog(self.app, _(u"no. %s of %s") % (self._item.serial, self._item.project.name),
                                   _(u"How many parts are required?"),
                                   0)
        self._item_editor = ItemEditor(a, store, item = item)

    def header(self, args = None):
        return self._item_editor.header() + self._item_editor.rows() + [urwid.Divider(" ")] + GenericSelector.header(self, args)

    @property
    def conditions(self):
        return [self.MODEL.item == self._item]

    def add(self, widget, id):
        return SearchForParts(self.app, self.store, action = ItemAssigner, action_kwargs = {"item": self._item})

    def edit(self, widget, id):
        self._amdlg.value = widget._data.count
        if not self.app.run_dialog(self._amdlg):
            return
        if widget._data.count != self._amdlg.value:
            widget._data.count = self._amdlg.value
            self.store.commit()
        return self.REFRESH

    def select(self, widget, id):
        # select the part pile to get parts from
        return AssignmentPartSelector(self.app, self.store, assignment = widget._data)

    @property
    def title(self):
        """Method called after show, returns new window footer."""
        return _(u"Part types assigned to %s in project %s" % (self._item.serial, self._item.project.name))


class ItemEditor(GenericEditor):
    MODEL = model.Item
    FIELDS = [
        (_(u"Serial no: "), "serial", Edit, {}, u""),
        (_(u"Kit: "), "kit", CheckBox, {}, False),
        (_(u"Description: "), "description", Edit, {"multiline": True}, u""),
        ]

    def __init__(self, a, store, item = None, caller = None):
        if item is None:
            item = self.MODEL()
            item.kit = False
            item.serial = u""
            item.description = u""
            item.project = caller.project
            item.history = model.History()
            item.history.event = model.History.NEW

        GenericEditor.__init__(self, a, store, item)

    @property
    def title(self):
        """Method called after show, returns new window title."""
        return _(u"Edit item")


class ItemSelector(GenericSelector):
    EDITOR = ItemEditor
    MODEL = model.Item
    FIELDS = [
        (_(u"id"), "fixed", 5, "id"),
        (_(u"serial no."), "weight", 1, "serial"),
        (_(u"kit"), "fixed", 3, "kit"),
        (_(u"changed"), "fixed", 10, "history.date"),
        (_(u"added"), "fixed", 10, "history.beginning.date")
        ]

    def __init__(self, a, store, project):
        GenericSelector.__init__(self, a, store)
        self._project = project
        self._project_editor = ProjectEditor(a, store, item = project)

    def header(self, args = None):
        return self._project_editor.header() + self._project_editor.rows() + [urwid.Divider(" ")] + GenericSelector.header(self, args)

    @property
    def conditions(self):
        return [self.MODEL.project == self._project]

    @property
    def project(self):
        return self._project

    def select(self, widget, id):
        return AssignmentSelector(self.app, self.store, item = widget._data)

    @property
    def title(self):
        """Method called after show, returns new window title."""
        return _(u"Items belonging to project %s") % self._project.name

class ProjectEditor(GenericEditor):
    MODEL = model.Project

    @property
    def title(self):
        """Method called after show, returns new window title."""
        return _(u"Edit project")


class ProjectSelector(GenericSelector):
    EDITOR = ProjectEditor
    MODEL = model.Project
    FIELDS = [
        (_(u"started"), "fixed", 10, "started"),
        (_(u"name"), "weight", 1, "name"),
        (_(u"summary"), "weight", 3, "summary"),
        (_(u"cnt"), "fixed", 3, "count_items")
        ]

    def select(self, widget, id):
        return ItemSelector(self.app, self.store, project = widget._data)

    @property
    def title(self):
        """Method called after show, returns new window title."""
        return _(u"Select project")
