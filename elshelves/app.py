import urwid
import urwid.raw_display
import urwid.web_display
import weakref
import re
import edit
from dialog import Dialog
from confirm_dialog import ConfirmDialog

class PopUpEnabledFrame(urwid.PopUpLauncher):
    def __init__(self, original_widget):
        self.__super.__init__(original_widget)
        self._dialogs = []
        self._dialog_sizes = []

    def show_dialog(self, dialog_instance, sizes):
        self._dialogs.append(dialog_instance)
        self._dialog_sizes.append(sizes)
        self.open_pop_up()

    def hide_dialog(self, dialog_instance):
        closed_dialog = self._dialogs.pop()
        assert closed_dialog == dialog_instance
        self._dialog_sizes.pop()
        if self._dialogs == []:
            self.close_pop_up()
        else:
            self.open_pop_up()

    @property
    def current_dialog(self):
        return self._dialogs[-1]

    def set_body(self, w):
        return self._original_widget.set_body(w)

    def create_pop_up(self):
        """
        Subclass must override this method and have is return a widget
        to be used for the pop-up.  This method is called once each time
        the pop-up is opened.
        """
        self._dialogs[-1].pre_open()
        return self._dialogs[-1]

    def get_pop_up_parameters(self):
        """
        Subclass must override this method and have it return a dict, eg:

        {'left':0, 'top':1, 'overlay_width':30, 'overlay_height':4}

        This method is called each time this widget is rendered.
        """
        return self._dialog_sizes[-1]


class App(object):
    palette = [
        # base screen color and its selection inverted variant
        ('body','white','dark cyan', 'standout'),

        # header and footer color
        ('header','white','dark red', 'bold'),
        ('footer','white','dark red', 'bold'),

        # edit field
        ('edit','black', 'light blue'), # inactive
        ('edit_f','white', 'dark blue'), # focused
        ('edit_c','black','light gray', 'standout'), # read only
        ('edit_fc','black', 'white', 'bold'), # read only focus

        # selected item in browser
        ('list_f','light gray', 'dark blue'), # focused

        # part header
        ('part_f', 'black', 'white', "standout"),
        ('part', 'black', 'light gray'),

        # button
        ('button','dark blue','white'),
        ('button_f','white','black','bold'),
        ]

    screen = None

    def __init__(self, title):
        self._title = title
        self._setup(title)

        self._header = urwid.AttrWrap(urwid.Text(title), 'header')
        self._footer = urwid.AttrWrap(urwid.Text(title), 'header')
        frame = urwid.Frame(None, header=self._header, footer=self._footer)
        self._frame = PopUpEnabledFrame(frame)

        # screen stack contains triplets
        #  UIScreen to show
        #  arguments for it's show method
        #  value indicating whether new mainloop is needed - None = do nothing, True = execute, False = already running, exit when window closes
        self._screens = []

    def switch_screen(self, ui, args = None):
        oldscr, oldattr, oldloop = self._screens.pop()
        self._screens.append((ui, args, oldloop))
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
            if oldscr != scr:
                self.debug()

        # we are in modal window, end it's loop
        assert oldloop != True # this cannot happen, if we are closing the window, the loop must be running
        if oldloop == False:
            raise urwid.ExitMainLoop()

        if self._screens:
            self.redraw()
        else:
            raise urwid.ExitMainLoop()

    def run_dialog(self, dialog):

        sizes = dialog.dialog_size()
        self._frame.show_dialog(dialog, sizes)

        self.run(self.dialog_input)
        self._frame.hide_dialog(dialog)
        return dialog.result

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

        title = screen.title or self._title or u""
        footer = screen.footer or u""

        if body:
            body = urwid.AttrMap(body, {"default": "body",
                                        None: "body",
                                        "": "body"})
            self._frame.set_body(body)
            self._header.set_text(title)
            self._footer.set_text(footer)

        if newloop == True:
            self._screens.pop()
            self._screens.append((screen, args, False))
            self.run()

    def run(self, input_handler = None):
        if input_handler is None:
            input_handler = self.input

        urwid.MainLoop(self._frame, self.palette, self.screen,
                       unhandled_input=input_handler,
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

    def dialog_input(self, key):
        dialog  = self._frame.current_dialog
        if dialog and key == 'esc':
            dialog.cancel()
            return True

        if dialog and key == 'enter':
            dialog.ok()
            return True

        return False

    def input(self, key):
        """Method called to process unhandled input key and mouse presses."""

        if self._screens:
            key = self._screens[-1][0].input(key)
            if key is None:
                return True

        if self._screens and key == 'esc':
            self.close_screen()
            return True

    @property
    def frame(self):
        return self._frame


class UIScreen(object):
    CONFIRM_CLOSE = None

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
            self.confirm(self.app.switch_screen, self._back, back_args)
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

    def confirm(self, cb, *args, **kwargs):
        if self.CONFIRM_CLOSE:
            confirmdlg = ConfirmDialog(self.app, _("Confirm close"),
                                _(self.CONFIRM_CLOSE),
                                yes = "Close", no = "Keep open")

            if self.app.run_dialog(confirmdlg):
              return cb(*args, **kwargs)
        else:
            return cb(*args, **kwargs)

    def close(self):
        self.confirm(self.app.close_screen)

    @property
    def footer(self):
        """Method called after show, returns new window footer."""
        pass

    @property
    def title(self):
        """Method called after show, returns new window title."""
        pass


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

def setextattr(obj, attr, val):
    """Allow saving to objects referenced from
       obj by attr.

       Standard setattr does not allow
         setattr(obj, "arg.arg2.arg3", value)
    """
    attrs = attr.split(".")
    for attr in attrs[:-1]:
        obj = getattr(obj, attr)
    setattr(obj, attrs[-1], val)

def save(self):
    """Save the value to the binded data object."""
    assert hasattr(self, "_bind") and self._bind
    (obj, attr) = self._bind
    assert type(self.edit_text) == unicode
    setextattr(obj, attr, self.edit_text)

def valuesave(self):
    """Save the value to the binded data object."""
    assert hasattr(self, "_bind") and self._bind
    (obj, attr) = self._bind
    setextattr(obj, attr, self.value())

def checksave(self):
    """Save the value to the binded data object."""
    assert hasattr(self, "_bind") and self._bind
    (obj, attr) = self._bind
    setextattr(obj, attr, self.get_state())


urwid.Edit.bind = bind
urwid.Edit.bind_live = bind_live
urwid.Edit._bind_live_cb = _bind_live_cb
urwid.Edit.reg = reg
urwid.Edit.save = save

edit.EmacsIntEdit.save = valuesave
edit.DateEdit.save = valuesave
edit.FloatEdit.save = valuesave

urwid.CheckBox.bind = bind
urwid.CheckBox.bind_live = bind_live
urwid.CheckBox._bind_live_cb = _bind_live_cb
urwid.CheckBox.reg = reg
urwid.CheckBox.save = checksave

urwid.Text.bind = lambda self,x,y: self
urwid.Text.reg = lambda self,x: self

def Button(content, *args, **kwargs):
    return urwid.AttrWrap(urwid.Button(content, *args, **kwargs), "button", "button_f")

def Edit(label, content, *args, **kwargs):
    return edit.EmacsEdit(label, content, *args, **kwargs)

def IntEdit(label, content, align = "left", *args, **kwargs):
    w = edit.EmacsIntEdit(label, content, *args, **kwargs)
    w.set_align_mode(align)
    return w

def FloatEdit(label, content, align = "left", *args, **kwargs):
    w = edit.FloatEdit(label, content, *args, **kwargs)
    w.set_align_mode(align)
    return w

def DateEdit(label, content, *args, **kwargs):
    return edit.DateEdit(label, content, *args, **kwargs)

def CheckBox(label, content, *args, **kwargs):
    return urwid.CheckBox(label, content, *args, **kwargs)

def Text(label, content, *args, **kwargs):
    if "multiline" in kwargs:
        del kwargs["multiline"]
    return urwid.Text(u"%s%s" % (label, content), *args, **kwargs)
