from storm.locals import create_database, Desc, Storm, Unicode, Int, Bool, DateTime, Date, Reference, ReferenceSet, Store, Float, Or
from storm.properties import PropertyColumn
from storm.databases.sqlite import SQLite
from storm.database import register_scheme
import os.path
import datetime
import unicodedata

SortableBase = PropertyColumn

class Tag(Storm):
    """Model for tags"""
    __storm_table__ = "tags"

    id = Int(primary=True)
    name = Unicode()
    summary = Unicode()
    description = Unicode()

class Footprint(Storm):
    """Model for one footprint"""
    __storm_table__ = "footprints"

    id = Int(primary=True)
    name = Unicode()
    summary = Unicode()
    description = Unicode()

    pins = Int()
    holes = Int() # no. of connected+unconnected holes to PCB
    kicad = Unicode() # formatting string using %d to be replaced by the number of pins from part

    def __str__(self):
        return "<Footprint id:%d name:%s holes:%s pins:%d>" % (self.id,
                                                             self.name,
                                                             self.holes,
                                                             self.pins)

class Price(Storm):
    """Model for pricing based on amount requested with history"""
    __storm_table__ = "prices"
    __storm_primary__ = "id", "time", "amount"

    id = Int()
    time = DateTime()
    amount = Int()
    price = Float()
    vat = Float() # in percents or Null if included
    currency = Unicode()

class Source(Storm):
    """Model for one source/vendor of parts"""
    __storm_table__ = "sources"

    id = Int(primary=True)
    name = Unicode()
    shortname = Unicode()
    summary = Unicode()
    description = Unicode()

    vat = Float() # default vat in percents or None if included in prices

    home = Unicode() # homepage
    url = Unicode() # formatting string with %s to be replaced by part id to get direct url
    prices = Unicode() # reference to somethign which will be able to retrieve prices
    customs = Bool() # is the shipment going through customs? (VAT?)

    def __init__(self, name, shortname, summary, description, home, url):
        self.name = name
        self.shortname = shortname
        self.summary = summary
        self.description = description
        self.home = home
        self.url = url

    def __str__(self):
        return "<Source %s id:%d name:%s home:%s" % (self.shortname,
                                                     self.id,
                                                     self.name,
                                                     self.home)

class PartSource(Storm):
    """Model for many to many relationship between Source and PartType"""
    __storm_table__ = "types_sources"
    __storm_primary__ = "part_type_id", "source_id"

    part_type_id = Int()
    part_type = Reference(part_type_id, "PartType.id")
    source_id = Int()
    source = Reference(source_id, Source.id)

    sku = Unicode() # vendor's id of this part
    price_id = Int()
    prices = ReferenceSet(price_id, Price.id)

    def __str__(self):
        return "<PartSource part_type:%s source:%s sku:%s>" % (self.part_type.name,
                                                               self.source.name,
                                                               self.sku)

    @property
    def min_amount(self):
        q = self.prices.order_by(Desc(Price.time)).order_by(Price.amount).one()
        if q:
            return q.amount
        else:
            return 1

    @property
    def price(self):
        cheapest = self.prices.order_by(Desc(Price.time)).order_by(Price.amount).any()
        if cheapest:
            return cheapest
        else:
            return 0.0

class PartType(Storm):
    """Model for one part type"""
    __storm_table__ = "types"

    id = Int(primary=True)
    name = Unicode(default=u"test")
    summary = Unicode(default=u"pokus")
    description = Unicode()

    footprint_id = Int()
    footprint = Reference(footprint_id, Footprint.id)
    sources = ReferenceSet(id, PartSource.part_type_id)
    parts = ReferenceSet(id, "Part.part_type_id")
    datasheet = Unicode()
    manufacturer = Unicode()

    def __str__(self):
        return "<PartType id:%d name:%s pins:%d footprint:%s>" % (self.id,
                                                                  self.name,
                                                                  self.footprint.pins,
                                                                  self.footprint)

    # This hook should reregister search terms after the Model is changed
    # but it is not working due to some strange error in Storm
    # so I am disabling it for now
    #def __storm_pre_flushed__(self):
    #    # update search term database after the change is flushed
    #    Term.register(self)

    @property
    def price(self):
        """find the lowest price"""
        return 0.0

    @property
    def count(self):
        """get the count of all components with this type"""
        if not Store.of(self):
            return 0

        return self.find_all.find(Part.assignment == None, Part.soldered == False).sum(Part.count) or 0

    @property
    def count_w_assigned(self):
        """get the count of all components with this type"""
        if not Store.of(self):
            return 0

        return self.find_all.find(Part.soldered == False).sum(Part.count) or 0


    @property
    def find_all(self):
        """get the list of all usable components with this type"""
        return Store.of(self).find(Part, Part.part_type_id == self.id, Part.usable == True)

class Location(Storm):
    """Model for locations"""
    __storm_table__ = "locations"

    id = Int(primary=True)
    name = Unicode(default=u"test")
    summary = Unicode(default=u"pokus")
    description = Unicode()


class History(Storm):
    """Model for historical records"""
    __storm_table__ = "history"

    INCOMING = 0
    NEW = 1
    MOVED = 2
    UPDATED = 3
    USED = 4
    DESTROYED = 5
    TESTED = 6
    SHIPPED = 7

    id = Int(primary=True)
    parent_id = Int()
    parent = Reference(parent_id, "History.id")
    time = DateTime()
    event = Int()
    description = Unicode()
    location_id = Int()
    location = Reference(location_id, Location.id)

    @property
    def beginning(self):
        oldest = self
        while oldest.parent:
            oldest = oldest.parent
        return oldest

    @property
    def date(self):
        return self.time.date()

class Part(Storm):
    """Model for a group of identical parts"""
    __storm_table__ = "parts"

    id = Int(primary=True)
    count = Int()
    source_id = Int()
    source = Reference(source_id, Source.id)
    date = Date()
    price = Float()
    vat = Float() # in percents or None if included in price
    part_type_id = Int()
    part_type = Reference(part_type_id, PartType.id)
    assignment_id = Int()
    assignment = Reference(assignment_id, "Assignment.id")
    history_id = Int()
    history = Reference(history_id, History.id)
    soldered = Bool()
    usable = Bool(default = True)


    @property
    def assigned(self):
        return self.assignment is not None

    def take(self, count):
        """Take some amount of parts from this pile and return the object
        representing this amount. Everything gets copied over."""

        assert count > 0
        assert count <= self.count

        if count == self.count:
            return self

        take = Part()
        take.count = count
        self.count -= count

        take.source = self.source
        take.date = self.date
        take.price = self.price
        take.vat = self.vat
        take.part_type = self.part_type
        take.assignment = self.assignment
        take.history = self.history
        take.soldered = self.soldered
        take.usable = self.usable
        Store.of(self).add(take)

        return take

    def record_history(self, history):
        """Add record to the history attribute

        :param history: history object describing action
        :type history: instance of History class
        """
        history.parent = self.history
        self.history = history
        return self

    def __str__(self):
        return "<Part id:%d type:%s count:%d manufacturer:%s>" % (self.id,
                                                                  self.part_type.name,
                                                                  self.count,
                                                                  self.part_type.manufacturer)

class Project(Storm):
    """Model for project"""
    __storm_table__ = "projects"

    id = Int(primary=True)
    name = Unicode(default=u"test")
    summary = Unicode(default=u"pokus")
    description = Unicode()
    started = Date()
    items = ReferenceSet(id, "Item.project_id")

    def __init__(self, name = u"", summary = u"", description = u""):
        self.name = name
        self.summary = summary
        self.description = description

    @property
    def count_items(self):
        items = self.items.find().count()
        return items or 0


class Item(Storm):
    """Model for actual built items"""
    __storm_table__ = "items"

    id = Int(primary=True)
    kit = Bool() # was this put together as a kit or assembled version?
    description = Unicode()
    assignments = ReferenceSet(id, "Assignment.item_id")
    serial = Unicode()
    project_id = Int()
    project = Reference(project_id, Project.id)
    history_id = Int()
    history = Reference(history_id, History.id)

class Assignment(Storm):
    """Model for many to many relationship between Source and PartType"""
    __storm_table__ = "assignments"

    id = Int(primary=True)
    part_type_id = Int()
    part_type = Reference(part_type_id, PartType.id)
    parts = ReferenceSet(id, Part.assignment_id)
    item_id = Int()
    item = Reference(item_id, Item.id)
    count = Int()

    def __unicode__(self):
        return u"%s - %s" % (self.item.project.name, self.item.id)

    @property
    def count_assigned(self):
        assigned = self.parts.find().sum(Part.count)
        return assigned or 0

    @property
    def count_soldered(self):
        soldered = self.parts.find(soldered = True).sum(Part.count)
        return soldered or 0

    def assign(self, part_pile, maximum = None):
        """Takes a pile of parts (one Part row) and assigns it to this slot. If there is more in the pile, it gets splitted.

        :param part_pile: one Part object containing pile of parts to assign
        :type part_pile: instance of Part
        """

        assert self.part_type == part_pile.part_type

        if maximum is None:
            maximum = part_pile.count

        # how many can we actually assign
        count = min(maximum, part_pile.count, self.count - self.count_assigned)
        assert count >= 0

        if count == 0:
            return

        # there are enough parts, assign them
        pile = part_pile.take(count)
        pile.assignment = self

class TermTypeMapping(Storm):
    __storm_table__ = "terms_types"
    __storm_primary__ = "term_id", "type_id"
    term_id = Int()
    term = Reference(term_id, "Term.id")
    type_id = Int()
    type = Reference(type_id, PartType.id)

class Term(Storm):
    """Model for search term mapping."""
    __storm_table__ = "terms"

    id = Int(primary=True)
    term = Unicode()
    alias_for_id = Int()
    alias_for = Reference(alias_for_id, "Term.id")
    part_types = ReferenceSet(id, TermTypeMapping.term_id, TermTypeMapping.type_id, PartType.id)

    @staticmethod
    def split(word):
        return word.split()

    @staticmethod
    def simplify(word):
        """Strips diacritics from unicode string"""
        word = ''.join((c for c in unicodedata.normalize('NFD', word) if unicodedata.category(c) != 'Mn'))
        return word.lower()

    @classmethod
    def register(cls, part_type):
        store = Store.of(part_type)
        name = cls.split(part_type.name)
        summary = cls.split(part_type.summary)
        description = cls.split(part_type.description)
        manufacturer = cls.split(part_type.manufacturer)
        terms = []

        # register the search terms
        for word in name + summary + description + manufacturer:
            word = cls.simplify(word)

            term = store.find(Term, term=word).any()
            if term is None:
                term = Term()
                term.term = word
                store.add(term)
            else:
                while term.alias_for:
                    term = term.alias_for

            if part_type not in term.part_types:
                term.part_types.add(part_type)

            terms.append(term)

        terms = set(terms)

        # remove stale search terms for updated object
        # skip for new object
        if part_type.id:
            mappings = store.find(TermTypeMapping, type=part_type)
            for mapping in mappings:
                if mapping.term not in terms:
                    store.remove(mapping)

        return terms

    @staticmethod
    def search(store, search_string):
        results = set()
        first_result = True
        negate_list = []

        for w in Term.split(search_string):
            if w.startswith("-"):
                w = w[1:]
                negate = True
            else:
                negate = False

            if w.startswith("\"") and w.endswith("\""):
                exact = True
                w = w[1:-1]
            else:
                exact = False

            w = Term.simplify(w).lower()

            if exact:
                terms = store.find(Term, term=w)
            else:
                terms = store.find(Term, Term.term.like("%%%s%%" % w))

            intermediate_result = set()
            for term in terms:
                intermediate_result.update(set(term.part_types))
                while term.alias_for:
                    term = term.alias_for
                    intermediate_result.update(set(term.part_types))

            if not negate:
                if first_result:
                    results = intermediate_result
                    first_result = False
                else:
                    results.intersection_update(intermediate_result)
            else:
                negate_list.append(intermediate_result)

        for neg in negate_list:
            results.difference_update(neg)

        return results

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

class RawPart(Struct):
    def __init__(self, extra = None):
        p = {
            "part_type": None,
            "search_name": u"",
            "name": u"",
            "summary": u"",
            "description": u"",
            "footprint": u"",
            "pins": 0,
            "manufacturer": u"",
            "sku": u"",
            "count": 0,
            "date": None,
            "unitprice": 0,
            "vat": None,
            "source": None,
            "datasheet": u"",
            "matches": []
            }

        if extra:
            p.update(extra)

        Struct.__init__(self, **p)

    def load(self, part_type):
        self.__dict__.update({
            "name": part_type.name,
            "summary": part_type.summary,
            "description": part_type.description,
            "footprint": part_type.footprint.name,
            "pins": part_type.pins,
            "manufacturer": part_type.manufacturer,
            "datasheet": part_type.datasheet
            })

class Meta(Storm):
    """Model for many to many relationship between Source and PartType"""
    __storm_table__ = "meta"

    key = Unicode(primary=True)
    value = Unicode()
    changed = DateTime()

class ForeignKeysSQLite(SQLite):
    """Set SQLite foreign key integrity mode. Has to be set
       on raw connection as storm.Store does too much magic with
       transactions"""

    def raw_connect(self):
        connection = SQLite.raw_connect(self)
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

def getStore(url, create = False):
    # register new Storm scheme
    register_scheme("sqlitefk", ForeignKeysSQLite)

    d = create_database(url)
    s = Store(d)

    if create:
        schema = file(os.path.join(os.path.dirname(__file__), "schema.sql"), "r").read().split("\n\n")
        for cmd in schema:
            s.execute(cmd)

        version = Meta()
        version.key = u"created"
        s.add(version)

        s.commit()

    return s


def fill_matches(store, data):
    search_name = data.search_name
    sku = data.sku
    manufacturer = data.manufacturer
    footprint = data.footprint
    source = data.source

    parts = []
    #if search_name:
    #    name_parts = search_name.split()
    #    for name_part in name_parts:
    #        parts.append(list(store.find(PartType, Or(
    #                        PartType.name.like("%%%s%%" % name_part, "$", False),
    #                        PartType.summary.like("%%%s%%" % name_part, "$", False),
    #                        PartType.description.like("%%%s%%" % name_part, "$", False)))
    #                     .config(distinct = True)
    #                     .values(PartType.id)))

    if search_name:
        parts.append([part_type.id for part_type in Term.search(store, search_name)])

    if sku:
        args = [ PartSource.sku.like("%s%%" % sku, "$", False) ]
        if source is not None:
            args.append(PartSource.source == source)

        # do not filter by source unless we are also checking for sku
        result = list(store.find(PartSource, *args)
                           .config(distinct = True)
                           .values(PartSource.part_type_id))

        # do not filter by sku if no such vendor/sku was found - we might be shopping somewhere else now
        if result:
            parts.append(result)

    if manufacturer:
        parts.append(list(store.find(PartType, Or(PartType.manufacturer == u"",
                                                  PartType.manufacturer.like("%%%s%%" % manufacturer, "$", False)))
                     .config(distinct = True)
                     .values(PartType.id)))

    if footprint:
        parts.append(list(store.find((PartType, Footprint),
                                Footprint.name.like("%%%s%%" % footprint, "$", False),
                                PartType.footprint_id == Footprint.id)
                     .config(distinct = True)
                     .values(PartType.id)))

    if hasattr(data, "item"):
        parts.append(list(
            store.find(Assignment, Assignment.item == data.item)
            .config(distinct = True).values(Assignment.part_type_id)))

    if hasattr(data, "project"):
        parts.append(list(
            store.find((Assignment, Item), Assignment.item == Item.id, Item.project == data.project)
            .config(distinct = True).values(Assignment.part_type_id)))

    # create a set containing all part types which matched all queries
    if parts:
        res = set(parts[0])
    else:
        res = set()

    for p in parts[1:]:
        res = res.intersection(set(p))

    data.matches = res

    return data

def debug(stream):
    import storm.tracer
    storm.tracer.debug(True, stream)
