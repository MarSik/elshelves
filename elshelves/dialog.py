import urwid

class Dialog(urwid.WidgetWrap):
    def __init__(self, app, contents):
        self.__super.__init__(contents)
        self._result = None
        self._app = app

    @property
    def app(self):
        return self._app

    def pre_open(self):
        self._result = None

    @property
    def result(self):
        return self._result

    def ok(self):
        pass

    def cancel(self):
        pass

    def close(self):
        raise urwid.ExitMainLoop()

    def dialog_size(self):
        raise Exception("Mus be implemented in subclass")
