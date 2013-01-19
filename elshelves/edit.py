import re
import datetime
import urwid
from urwid import command_map, CompositeCanvas, Text

command_map["ctrl a"] = "cursor max left"
command_map["ctrl e"] = "cursor max right"

class EmacsEdit(urwid.Edit):
    signals = ["enter"] + urwid.Edit.signals

    def keypress(self, size, key):
        if key == "ctrl k":
            p = self.edit_pos
            self.set_edit_text(self._edit_text[:p])
        elif key == "ctrl g":
            self.highlight = None
        elif key == "enter" and not self.multiline:
            self._emit("enter")
        else:
            return urwid.Edit.keypress(self, size, key)

class FloatEdit(EmacsEdit):
    """Edit widget for float values"""

    # this should probably just be "valid_char()", but was renamed for reasons
    # stated below.
    def valid_charkey(self, ch):
        """
        Return true for valid float characters, regardless of position
        """
        allowed = "0123456789.-+eE"
        if self.allow_nan:
            # allow "NaN", "nan", "Infinity", and "infinity"
            allowed +="NnaIifty"
        return len(ch)==1 and ch in allowed

    # note, this should probably be renamed "valid_result()", and the base
    # class should be modified to call it by its new name.  That would make
    # it so that "valid_charkey()" could be named "valid_char()".  This
    # function is currently named the way it is so that this class will run
    # on an unmodified release of urwid.
    def valid_char(self, ch):
        """
        Return true if the result would be a valid string representing a float,
        or at least a partial representation of a float
        """

        future_result, future_col=self.insert_text_result(ch)

        if not self.valid_charkey(ch):
            return False

        # if the result is a fully valid float, return true:
        if re.match(r'[\+\-]?(0|[1-9]\d*)(\.\d+)?([eE][\+\-]?\d+)?$', future_result):
            return True

        if self.allow_nan:
            # allow partial versions of "NaN"/"nan" and "[Ii]nfinity"
            if re.match(r'[\+\-]?[Ii](n(f(i(n(i(t(y)?)?)?)?)?)?)?$', future_result):
                return True
            if re.match(r'[Nn](a([Nn])?)?$', future_result):
                return True

        # if the result would be mostly valid, still return true so that the
        # user can finish typing:

        # Partial exponent
        if re.match(r'-?(0|[1-9]\d*)(\.\d+)?([eE][\+\-]?)?$', future_result):
            return True

        # Partial decimal
        if re.match(r'-?(0|[1-9]\d*)(\.)?([eE])?$', future_result):
            return True

        # Prohibit leading zero in front of any digit at the beginning of the
        # input
        if re.match(r'-?0\d+', future_result):
            return False

        # Partial whole number
        if re.match(r'-?(\d*)(\.\d+)?([eE])?$', future_result):
            return True

        return False

    def __init__(self,caption="",default=None, allow_nan=True, allow_none = False):
        """
        caption -- caption markup
        default -- default edit value

        >>> FloatEdit("", 42)
        <FloatEdit selectable flow widget '42' edit_pos=2>
        """
        if default is not None: val = str(default)
        else: val = ""
        self.has_focus=False
        self.allow_nan=allow_nan
        self.__super.__init__(caption,val)
        self.allow_none = allow_none

    def keypress(self, size, key):
        """
        Handle editing keystrokes.  Remove leading zeros.

        >>> e, size = IntEdit("", 5002), (10,)
        >>> e.keypress(size, 'home')
        >>> e.keypress(size, 'delete')
        >>> e.edit_text
        '002'
        >>> e.keypress(size, 'end')
        >>> e.edit_text
        '2'
        """
        (maxcol,) = size
        unhandled = EmacsEdit.keypress(self,(maxcol,),key)

        return unhandled

    def value(self):
        """
        Return the numeric value of self.edit_text.
        """
        if self.edit_text:
            return float(self.edit_text)
        elif self.allow_none:
            return None
        else:
            return 0

    def on_blur(self):
        """
        Called when the widget loses focus
        """
        newtext=self.edit_text

        # This function relies on valid_char() to do the heavy lifting.  The
        # code below performs cleanup on partial entries.

        # Nuke partial exponent
        newtext=re.sub(r'[eE][\+\-]?$', '', newtext)

        # If the 'e' is missing, put it back
        newtext=re.sub(r'(\d+)([\+\-])', r'\1e\2', newtext)

        # assume n* is "nan"
        newtext=re.sub(r'^[Nn].*$', 'nan', newtext)
        # assume i* is "inf"
        newtext=re.sub(r'^([\+\-]?)[Ii].*$', r'\1inf', newtext)
        # nuke "finity" or "an"
        newtext=re.sub(r'^[afty].*', '', newtext)

        if newtext=="":
            newtext="0"

        # inlining function snarfed from http://bugs.python.org/msg75745
        def isNaN(x):
            return (x is x) and (x != x)

        if not self.allow_nan and (isNaN(float(newtext)) or
                                   float(newtext)==float('-inf') or
                                   float(newtext)==float('inf')):
            newtext="0"

        newtext=str(float(newtext))
        newtext=re.sub(r'\.0$', '', newtext)

        self.set_edit_text(newtext)

    # This retrofits an on_blur() method into the class, and isn't specific
    # to FloatEdit
    def render(self,(maxcol,), focus=False):
        if self.has_focus and not focus:
            self.has_focus=False
            self.on_blur()
        self.has_focus=focus

        return self.__super.render((maxcol,), focus=focus)

class DateEdit(EmacsEdit):
    """Edit widget for date values"""

    VALID_DATE = re.compile(r"^(19|20)[0-9]{2}(0[1-9]|10|11|12)(([012][0-9])|30|31)$")
    VALID_PARTIAL_DATE = re.compile(r"^(1(9|$)|2(0|$))([0-9]([0-9]|$)|$)(0([1-9]|$)|1([012]|$)|$)([012]([0-9]|$)|3([01]|$)|$)$")

    # this should probably just be "valid_char()", but was renamed for reasons
    # stated below.
    def valid_charkey(self, ch):
        """
        Return true for valid date characters, regardless of position
        """
        allowed = "0123456789"
        return len(ch)==1 and ch in allowed

    # note, this should probably be renamed "valid_result()", and the base
    # class should be modified to call it by its new name.  That would make
    # it so that "valid_charkey()" could be named "valid_char()".  This
    # function is currently named the way it is so that this class will run
    # on an unmodified release of urwid.
    def valid_char(self, ch):
        """
        Return true if the result would be a valid string representing a date,
        or at least a partial representation of a date
        """

        if not self.valid_charkey(ch):
            return False

        future_result, future_pos=self.insert_text_result(ch)

        if len(future_result) > 8:
            return False

        # if the result is a fully valid date, return true:
        if self.VALID_DATE.match(future_result):
            return True

        # if the result would be mostly valid, still return true so that the
        # user can finish typing:
        if self.VALID_PARTIAL_DATE.match(future_result):
            return True

        return False

    def __init__(self,caption=u"",default=None, mask=u"YYYY-mm-dd"):
        """
        caption -- caption markup
        default -- default edit value
        """
        self._date_mask = mask

        if default is not None: val = u"%04d%02d%02d" % (default.year, default.month, default.day)
        else: val = u""

        self.has_focus=False
        self.__super.__init__(caption,val)

    def keypress(self, size, key):
        """
        Handle editing keystrokes.  Remove leading zeros.

        >>> e, size = IntEdit("", 5002), (10,)
        >>> e.keypress(size, 'home')
        >>> e.keypress(size, 'delete')
        >>> e.edit_text
        '002'
        >>> e.keypress(size, 'end')
        >>> e.edit_text
        '2'
        """
        (maxcol,) = size
        unhandled = EmacsEdit.keypress(self,(maxcol,),key)

        return unhandled

    def value(self):
        """
        Return the numeric value of self.edit_text.
        """
        if self.VALID_DATE.match(self.edit_text):
            return datetime.date(int(self.edit_text[0:4]),
                                 int(self.edit_text[4:6]),
                                 int(self.edit_text[6:8]))
        else:
            return None

    def on_blur(self):
        """
        Called when the widget loses focus
        """
        newtext=self.edit_text

        self.set_edit_text(newtext)

    def get_text(self):
        """
        Returns (text, attributes).

        text -- complete text of caption and edit_text, maybe masked away
        attributes -- run length encoded attributes for text
        """

        mask = list(self._date_mask)

        year = self._edit_text[0:4]
        month = self._edit_text[4:6]
        day = self._edit_text[6:8]

        mask[0:len(year)] = year
        mask[5:5+len(month)] = month
        mask[8:8+len(day)] = day

        mask = u"".join(mask)

        return self._caption + mask, self._attrib

    def get_cursor_coords(self, maxsize):
        x, y = EmacsEdit.get_cursor_coords(self, maxsize)
        oldx = x
        if oldx >= 4:
            x = x + 1
        if oldx >= 6:
            x = x + 1
        return x, y

    def render(self, size, focus=False):
        """
        Render edit widget and return canvas.  Include cursor when in
        focus.

        >>> c = Edit("? ","yes").render((10,), focus=True)
        >>> c.text # ... = b in Python 3
        [...'? yes     ']
        >>> c.cursor
        (5, 0)
        """
        if self.has_focus and not focus:
            self.has_focus=False
            self.on_blur()
        self.has_focus=focus

        (maxcol,) = size
        self._shift_view_to_cursor = bool(focus)

        canv = Text.render(self,(maxcol,))
        if focus:
            canv = CompositeCanvas(canv)
            canv.cursor = self.get_cursor_coords((maxcol,))

        # .. will need to FIXME if I want highlight to work again
        #if self.highlight:
        #    hstart, hstop = self.highlight_coords()
        #    d.coords['highlight'] = [ hstart, hstop ]
        return canv

    def keypress(self, size, key):
        if key == "tab":
            date = datetime.date.today()
            p = self.edit_pos
            if p<4:
                self.set_edit_text(u"%04d" % date.year)
            elif p<6:
                self.set_edit_text(self.edit_text[:4] + u"%02d" % date.month)
            elif p<8:
                self.set_edit_text(self.edit_text[:6] + u"%02d" % date.day)
            self.set_edit_pos(len(self.edit_text))
        else:
            return EmacsEdit.keypress(self, size, key)

class EmacsIntEdit(EmacsEdit):
    """Edit widget for integer values"""

    def valid_char(self, ch):
        """
        Return true for decimal digits.
        """
        return len(ch)==1 and ch in "0123456789"

    def __init__(self,caption="",default=None, allow_none = False):
        """
        caption -- caption markup
        default -- default edit value

        >>> IntEdit(u"", 42)
        <IntEdit selectable flow widget '42' edit_pos=2>
        """
        if default is not None: val = str(default)
        else: val = ""
        self.__super.__init__(caption,val)
        self.allow_none = allow_none

    def keypress(self, size, key):
        """
        Handle editing keystrokes.  Remove leading zeros.

        >>> e, size = IntEdit(u"", 5002), (10,)
        >>> e.keypress(size, 'home')
        >>> e.keypress(size, 'delete')
        >>> print e.edit_text
        002
        >>> e.keypress(size, 'end')
        >>> print e.edit_text
        2
        """
        (maxcol,) = size
        unhandled = EmacsEdit.keypress(self,(maxcol,),key)

        if not unhandled:
        # trim leading zeros
            while len(self.edit_text) > 1 and \
                  self.edit_pos > 0 and \
                  self.edit_text[:1] == "0":
                self.set_edit_pos(self.edit_pos - 1)
                self.set_edit_text(self.edit_text[1:])

        return unhandled

    def value(self):
        """
        Return the numeric value of self.edit_text.

        >>> e, size = IntEdit(), (10,)
        >>> e.keypress(size, '5')
        >>> e.keypress(size, '1')
        >>> e.value() == 51
        True
        """
        if self.edit_text:
            return long(self.edit_text)
        elif self.allow_none:
            return None
        else:
            return 0
