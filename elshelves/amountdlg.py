import urwid
import app

class AmountDialog(app.Dialog):
    def _ok(self, button):
        self._value = self.edit_field.value()
        self.close()

    def _cancel(self, button):
        self.close()

    def __init__(self, title, description, default = 0, cb = None, args = None):
        self.title = title
        self.description = description
        self._value = default
        self.cb = cb
        self.args = args

        self.edit_field = app.IntEdit(u"", self.value)
        ok_button = app.Button(_("OK"), self._ok)
        cancel_button = app.Button(_("Cancel"), self._cancel)

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
