import urwid
import app
import dialog

class ConfirmDialog(dialog.Dialog):
    def ok(self, button = None):
        self._result = True
        self.close()

    def cancel(self, button = None):
        self._result = False
        self.close()

    def __init__(self, appinst, title, description, default = None,
                 cb = None, args = None, yes = "Yes", no = "No"):
        self.title = title
        self.description = description
        self.cb = cb
        self.args = args

        ok_button = app.Button(_(yes), self.ok)
        cancel_button = app.Button(_(no), self.cancel)

        pile = urwid.Pile([
            urwid.Text(self.description),
            urwid.Columns([ok_button, cancel_button], 3)
            ])

        header = urwid.AttrWrap(urwid.Text(self.title), "header")
        fill = urwid.Filler(pile)
        frame = urwid.Frame(fill, header = header)

        dialog = urwid.AttrWrap(frame, "dialog")
        self.__super.__init__(appinst, dialog)

    def dialog_size(self):
        return {"left": 10, "top": 10, "overlay_width": 60, "overlay_height": 10}
