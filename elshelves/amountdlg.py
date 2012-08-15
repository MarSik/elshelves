import urwid
import app
from edit import DateEdit

class AmountDialog(app.Dialog):
    EDIT_FIELD = app.IntEdit, {}

    def ok(self, button = None):
        self._value = self.edit_field.value()
        self.close()

    def cancel(self, button = None):
        self.close()

    def __init__(self, title, description, default = None, cb = None, args = None):
        self.title = title
        self.description = description
        self._value = default
        self.cb = cb
        self.args = args

        self.edit_field = self.EDIT_FIELD[0](u"", self.value, **self.EDIT_FIELD[1])
        length = len(self.edit_field.get_edit_text())
        self.edit_field.highlight = (0, length)
        urwid.connect_signal(self.edit_field, "enter", self.ok)

        ok_button = app.Button(_("OK"), self.ok)
        cancel_button = app.Button(_("Cancel"), self.cancel)

        pile = urwid.Pile([
            urwid.Text(self.description),
            self.edit_field,
            urwid.Columns([ok_button, cancel_button], 3)
            ])

        header = urwid.AttrWrap(urwid.Text(self.title), "header")
        fill = urwid.Filler(pile)
        frame = urwid.Frame(fill, header = header)

        dialog = urwid.AttrWrap(frame, "dialog")
        self.__super.__init__(dialog)

    def dialog_size(self):
        return {"left": 10, "top": 10, "overlay_width": 60, "overlay_height": 10}

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val
        self.edit_field.set_edit_text(str(val))

class DateDialog(AmountDialog):
    EDIT_FIELD = DateEdit, {"mask": _(u"YYYY-mm-dd")}
