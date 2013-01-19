import gettext
gettext.install('elshelves', unicode=1)

import os
import optparse

import urwid
import urwid.web_display
from version import __version__
import model
import app
from main import Actions
from part_selector import SearchForParts, PartCreator

def main():
    homedir = os.environ['HOME']
    confdir = os.path.join(homedir, ".elshelves")
    dbfile = os.path.join(confdir, "elshelves.sqlite3")

    parser = optparse.OptionParser()
    parser.add_option("--importorg", action="store", default = None)
    opts, args = parser.parse_args()

    # let me use different database file
    if args:
        dbfile = args[0]

    try:
        os.makedirs(confdir)
    except OSError as e:
        if e.errno != 17: # Already existing dir
            raise

    errlog = file(os.path.join(confdir, "error_log"), "w")
    model.debug(errlog)

    store = model.getStore("sqlitefk:%s" % dbfile,
                           create = not os.path.exists(dbfile))

    schema_version = store.get(model.Meta, u"version").value

    text_header = "Shelves %s (db %s)" % (__version__, schema_version)

    a = app.App(text_header)
    actions_screen = Actions(a, store)
    a.switch_screen_with_return(actions_screen)

    if opts.importorg:
        try:
            data = open(opts.importorg, "r").readlines()
            parts = []
            for l in data:
                if l.strip() == "":
                    continue
                l = [i.strip() for i in l[1:].split("|", 7)]

                source = store.find(model.Source,
                                    model.Source.name.like("%%%s%%" % l[3].decode("utf8"), "$", False)
                                    ).one()

                part = model.RawPart({
                    "search_name": l[0].decode("utf8"),
                    "count": int(l[1]),
                    "manufacturer": l[2].decode("utf8"),
                    "source": source,
                    "summary": l[4].decode("utf8"),
                    "footprint": l[5].decode("utf8"),
                    "description": l[6].decode("utf8")
                    })
                parts.append(part)

            dlg = SearchForParts(a, store,
                                 back=None, action=PartCreator,
                                 parts = parts)
            a.switch_screen_with_return(dlg)
        except:
            raise

    a.run()

if '__main__' == __name__ or urwid.web_display.is_web_request():
    main()
