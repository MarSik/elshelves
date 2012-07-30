from storm.locals import create_database, Desc, Storm, Unicode, Int, Bool, DateTime, Date, Reference, ReferenceSet, Store, Float
import os.path

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

    smd = Bool()
    pins = Int()
    kicad = Unicode() # formatting string using %d to be replaced by the number of pins from part

    def __str__(self):
        return "<Footprint id:%d name:%s smd:%s pins:%d>" % (self.id,
                                                             self.name,
                                                             str(self.smd),
                                                             self.pins)

class Price(Storm):
    """Model for pricing based on amount requested with history"""
    __storm_table__ = "prices"
    __storm_primary__ = "id", "time", "amount"

    id = Int()
    time = DateTime()
    amount = Int()
    price = Float()
    vat_included = Bool()
    currency = Unicode()

class Source(Storm):
    """Model for one source/vendor of parts"""
    __storm_table__ = "sources"

    id = Int(primary=True)
    name = Unicode()
    summary = Unicode()
    description = Unicode()

    home = Unicode() # homepage
    url = Unicode() # formatting string with %s to be replaced by part id to get direct url
    prices = Unicode() # reference to somethign which will be able to retrieve prices
    customs = Bool() # is the shipment going through customs? (VAT?)

    def __init__(self, name, summary, description, home, url):
        self.name = name
        self.summary = summary
        self.description = description
        self.home = home
        self.url = url

    def __str__(self):
        return "<Source id:%d name:%s home:%s" % (self.id,
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
            return price
        else:
            return 0.0

class PartType(Storm):
    """Model for one part type"""
    __storm_table__ = "types"

    id = Int(primary=True)
    name = Unicode(default=u"test")
    summary = Unicode(default=u"pokus")
    description = Unicode()


    pins = Int()
    footprint_id = Int()
    footprint = Reference(footprint_id, Footprint.id)
    sources = ReferenceSet(id, PartSource.part_type_id)
    parts = ReferenceSet(id, "Part.part_type_id")
    datasheet = Unicode()
    manufacturer = Unicode()

    def __str__(self):
        return "<PartType id:%d name:%s pins:%d footprint:%s>" % (self.id,
                                                                  self.name,
                                                                  self.pins,
                                                                  self.footprint)

    @property
    def price(self):
        """find the lowest price"""
        return 0.0

    @property
    def count(self):
        """get the count of all components with this type"""
        if not Store.of(self):
            return 0

        return Store.of(self).find(Part, Part.part_type_id == self.id).sum(Part.count)


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
    MOVED = 1
    UPDATED = 2
    USED = 3
    DESTROYED = 4
    TESTED = 5
    SHIPPED = 6

    id = Int(primary=True)
    parent = Reference(id, "History.id")
    time = DateTime()
    event = Int()
    description = Unicode()
    location_id = Int()
    location = Reference(location_id, Location.id)

class Part(Storm):
    """Model for a group of identical parts"""
    __storm_table__ = "parts"

    id = Int(primary=True)
    count = Int()
    source_id = Int()
    source = Reference(source_id, Source.id)
    date = Date()
    price = Float()
    part_type_id = Int()
    part_type = Reference(part_type_id, PartType.id)
    assignment_id = Int()
    assignment = Reference(assignment_id, "Assignment.id")
    history_id = Int()
    history = Reference(history_id, History.id)

    def __str__(self):
        return "<Part id:%d type:%s count:%d manufacturer:%s>" % (self.id,
                                                                  self.part_type.name,
                                                                  self.count,
                                                                  self.manufacturer)

class Project(Storm):
    """Model for project"""
    __storm_table__ = "projects"

    id = Int(primary=True)
    name = Unicode(default=u"test")
    summary = Unicode(default=u"pokus")
    description = Unicode()

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
    parts = ReferenceSet(id, Part.assignment_id)
    item_id = Int()
    item = Reference(item_id, Item.id)
    count = Int()

def getStore(url, create = False):
    d = create_database(url)
    s = Store(d)
    if url.startswith("sqlite:"):
        s.execute("PRAGMA foreign_keys = ON;")

    if create:
        schema = file(os.path.join(os.path.dirname(__file__), "schema.sql"), "r").read().split("\n\n")
        for cmd in schema:
            s.execute(cmd)
        s.commit()

    return s


def fill_matches(store, data):
    search_name = data.search_name
    sku = data.sku
    manufacturer = data.manufacturer
    footprint = data.footprint
    source = data.source

    parts = []
    if search_name:
        name_parts = search_name.split()
        for name_part in name_parts:
            parts.append(list(store.find(PartType,
                            PartType.name.like("%%%s%%" % name_part, True, False) or
                            PartType.summary.like("%%%s%%" % name_part, True, False) or
                            PartType.description.like("%%%s%%" % name_part, True, False))
                         .config(distinct = True)
                         .values(PartType.id)))

    if sku:
        args = [ PartSource.sku == sku ]
        if source is not None:
            args.append(PartSource.source == source)

        # do not filter by source unless we are also checking for sku
        parts.append(list(store.find(PartSource, *args)
                     .config(distinct = True)
                     .values(PartSource.part_type_id)))

    if manufacturer:
        parts.append(list(store.find(PartType, PartType.manufacturer.like("%%%s%%" % manufacturer, True, False))
                     .config(distinct = True)
                     .values(PartType.id)))

    if footprint:
        parts.append(list(store.find((PartType, Footprint),
                                Footprint.name.like("%%%s%%" % footprint, True, False),
                                PartType.footprint_id == Footprint.id)
                     .config(distinct = True)
                     .values(PartType.id)))

    # create a set containing all part types which matched all queries
    if parts:
        res = set(parts[0])
    else:
        res = set()

    for p in parts[1:]:
        res = res.intersection(set(p))

    data.matches = res

    return data
