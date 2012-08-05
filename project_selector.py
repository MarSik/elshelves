# encoding: utf8

import app
import urwid
import model
from selector import GenericSelector, GenericEditor
from part_selector import SearchForParts
from browser import PartBrowser
from app import Edit, IntEdit, CheckBox, Button
from amountdlg import AmountDialog

class AssignmentPartSelector(PartBrowser):
    def edit(self, widget, id):
        pass

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
                assert part.part_type is not None

                # known part, just assign new amount request of it
                if int(part.count) > 0:
                    new_part = model.Assignment()
                    new_part.part_type = part.part_type
                    new_part.item = self._item
                    new_part.count = int(part.count)
                    self.store.add(new_part)

                    # if there is only one unused pile of parts, assign it
                    piles = list(self.store.find(model.Part, part_type=part.part_type, assignment=None))
                    if len(piles) == 1:
                        new_part.assign(piles[0])

            self.store.commit()
        except Exception:
            self.app.debug()
            self.store.rollback()


class AssignmentSelector(GenericSelector):
    MODEL = model.Assignment
    EDITOR = None
    FIELDS = [
        (_(u"type"), "fixed", 15, "part_type.name"),
        (_(u"footprint"), "fixed", 10, "part_type.footprint.name"),
        (_(u"summary"), "weight", 1, "part_type.summary"),
        (_(u"manufacturer"), "fixed", 15, "part_type.manufacturer"),
        (_(u"count"), "fixed", 6, "count_assigned"),
        (_(u"required"), "fixed", 6, "count")
        ]

    def __init__(self, a, store, item):
        GenericSelector.__init__(self, a, store)
        self._item = item
        self._amdlg = AmountDialog(_(u"no. %s of %s") % (self._item.serial, self._item.project.name),
                                   _(u"How many parts are required?"),
                                   0)

    @property
    def conditions(self):
        return [self.MODEL.item == self._item]

    def add(self):
        return SearchForParts(self.app, self.store, action = ItemAssigner, action_kwargs = {"item": self._item})

    def edit(self, widget, id):
        self._amdlg.value = widget._data.count
        self.app.run_dialog(self._amdlg)
        widget._data.count = self._amdlg.value
        self.app.switch_screen(self)
        self.app.commit()

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
        (_(u"serial no."), "fixed", 20, "serial"),
        (_(u"kit"), "weight", 1, "kit"),
        (_(u"changed"), "fixed", 20, "history.time"),
        (_(u"added"), "fixed", 20, "history.beginning.time")
        ]

    def __init__(self, a, store, project):
        GenericSelector.__init__(self, a, store)
        self._project = project

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

    def select(self, widget, id):
        return ItemSelector(self.app, self.store, project = widget._data)

    @property
    def title(self):
        """Method called after show, returns new window title."""
        return _(u"Select project")
