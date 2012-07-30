import urwid
import urwid.raw_display
import urwid.web_display
import weakref

class App(object):
    palette = [
        ('body','black','light gray', 'standout'),
        ('reverse','light gray','black'),
        ('header','white','dark red', 'bold'),
        ('part header', 'black', 'light gray'),
        ('part header focus', 'black', 'white', 'standout'),
        ('important','dark blue','light gray',('standout','underline')),
        ('editfc','black', 'white', 'bold'),
        ('editbx','black', 'white'),
        ('editfc_f','white', 'dark blue', 'bold'),
        ('editbx_f','light gray', 'dark blue'),
        ('editcp','black','light gray', 'standout'),
        ('bright','dark gray','light gray', ('bold','standout')),
        ('buttn','black','dark cyan'),
        ('buttnf','white','dark blue','bold'),
        ]

    screen = None

    def __init__(self, title):
        self._setup(title)

        self._header = urwid.AttrWrap(urwid.Text(title), 'header')
        self._frame = urwid.Frame(None, header=self.header)

        self._footer = None

        # screen stack contains triplets
        #  UIScreen to show
        #  arguments for it's show method
        #  value indicating whether new mainloop is needed - None = do nothing, True = execute, False = already running, exit when window closes
        self._screens = []

    def switch_screen(self, ui, args = None):
        self._screens.pop()
        self._screens.append((ui, args, None))
        self.redraw()

    def switch_screen_with_return(self, ui, args = None):
        self._screens.append((ui, args, None))
        self.redraw()

    def switch_screen_modal(self, ui, args = None):
        self._screens.append((ui, args, True))
        self.redraw()
        self.redraw() # get back to the previous screen

    def close_screen(self, scr = None):
        oldscr, oldattr, oldloop = self._screens.pop()
        if scr is not None:
            assert oldscr == scr

        # we are in modal window, end it's loop
        assert oldloop != True # this cannot happen, if we are closing the window, the loop must be running
        if oldloop == False:
            raise urwid.ExitMainLoop()

        if self._screens:
            self.redraw()
        else:
            raise urwid.ExitMainLoop()

    def debug(self):
        if self.screen:
            self.screen.stop()
        import pdb
        pdb.set_trace()
        if self.screen:
            self.screen.start()

    def redraw(self):
        if not self._screens:
            return

        screen, args, newloop = self._screens[-1]
        body = screen.show(args)
        # TODO call screen.title
        if body:
            self._frame.set_body(body)

        if newloop == True:
            self._screens.pop()
            self._screens.append((screen, args, False))
            self.run()

    def run(self):
        urwid.MainLoop(self._frame, self.palette, self.screen,
                       unhandled_input=self.input,
                       pop_ups=True).run()

    def _setup(self, title):
        urwid.web_display.set_preferences(title)
        # try to handle short web requests quickly
        if urwid.web_display.handle_short_request():
            return

        # use appropriate Screen class
        if urwid.web_display.is_web_request():
            self.screen = urwid.web_display.Screen()
        else:
            self.screen = urwid.raw_display.Screen()

    def input(self, key):
        """Method called to process unhandled input key presses."""
        if self._screens:
            key = self._screens[-1][0].input(key)
            if key is None:
                return True

        if self._screens and key == 'esc':
            self.close_screen()
            return True

    @property
    def header(self):
        return self._header

    @property
    def store(self):
        return self._store


class UIScreen(object):
    def __init__(self, app, store, back = None, back_args = None):
        self._app = app
        self._store = store
        self._back = back
        self._back_args = back_args

    def show(self, args = None):
        """Method which is called before the screen is displayed. Is has to return the top level widget containing the contents."""
        pass

    def back(self, args = None):
        if self._back:
            if args is None:
                back_args = self._back_args
            else:
                back_args = args
            self.app.switch_screen(self._back, back_args)
        else:
            self.close()

    def input(self, key):
        """Method called to process unhandled input key presses."""
        if key == "esc":
            self.back()

    @property
    def store(self):
        return self._store

    @property
    def app(self):
        return self._app

    def close(self):
        self.app.close_screen(self)

    def title(self, old):
        """Method called after show, it gets the current window title and can return a new one."""
        return old


class Selectable(urwid.WidgetWrap):
    def __init__ (self, w):
        urwid.WidgetWrap.__init__(self, w)

    def selectable(self):
        return True

    def keypress(self, size, key):
        if self._w.selectable():
            return self._w.keypress(size, key)
        else:
            return key

class SaveRegistry(weakref.WeakKeyDictionary):
    def add(self, key):
        self[key] = 1

# modify urwid.Edit
def _bind_live_cb(self, widget, signal, target):
    """save data "change" signal handler, target is (object, attribute) to store changed data into"""
    (obj, attr) = target

    assert type(widget.edit_text) == unicode

    setattr(obj, attr, widget.edit_text)

def bind_live(self, target_obj, target_attr):
    """Connect the Edit object to a target_obj.target_attr and update it every time the Edit changes."""
    urwid.connect_signal(self, "change", self._bind_live_cb, (target_obj, target_attr))
    self._bind = (target_obj, target_attr)
    return self

def bind(self, target_obj, target_attr):
    """Connect the Edit object to a target_obj.target_attr."""
    self._bind = (target_obj, target_attr)
    return self

def reg(self, save_registry):
    """Add self to the list for the purpose of declaratively making a list of Edits to save."""
    save_registry.add(self)
    return self

def save(self):
    """Save the value to the binded data object."""
    assert hasattr(self, "_bind") and self._bind
    (obj, attr) = self._bind
    assert type(self.edit_text) == unicode
    setattr(obj, attr, self.edit_text)

urwid.Edit.bind = bind
urwid.Edit.bind_live = bind_live
urwid.Edit._bind_live_cb = _bind_live_cb
urwid.Edit.reg = reg
urwid.Edit.save = save
