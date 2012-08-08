import gettext
gettext.install('elshelves', unicode=1)

import os
import urwid
from version import __version__
import model
import app
from main import Actions

def main():
    homedir = os.environ['HOME']
    confdir = os.path.join(homedir, ".elshelves")
    dbfile = os.path.join(confdir, "elshelves.sqlite3")

    try:
        os.makedirs(confdir)
    except OSError as e:
        if e.errno != 17: # Already existing dir
            raise

    errlog = file(os.path.join(confdir, "error_log"), "w")
    model.debug(errlog)

    store = model.getStore("sqlite:%s" % dbfile, create = not os.path.exists(dbfile))

    schema_version = store.get(model.Meta, u"version").value

    text_header = "Shelves %s (db %s)" % (__version__, schema_version)

    a = app.App(text_header)
    actions_screen = Actions(a, store)
    a.switch_screen_modal(actions_screen)

if '__main__' == __name__ or urwid.web_display.is_web_request():
    main()
