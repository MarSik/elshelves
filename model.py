from storm.locals import create_database, Storm, Unicode, Int, Bool, DateTime, Date, Reference, ReferenceSet, Store, Float


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

class PartSource(object):
    """Model for many to many relationship between Source and PartType"""
    __storm_table__ = "types_sources"
    __storm_primary__ = "part_type_id", "source_id"

    part_type_id = Int()
    source_id = Int()
    source = Reference(source_id, Source.id)

    sku = Unicode() # vendor's id of this part
    price_id = Int()
    prices = ReferenceSet(price_id, Price.id)

    @property
    def min_amount(self):
        q = self.prices.order_by(Desc(Price.time)).order_by(Price.amount).one()
        if q:
            return q.amount
        else:
            return 1

    @property
    def price(self):
        return self.prices.order_by(Desc(Price.time)).order_by(Price.amount).all()

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

    id = Int(primary=True)
    log = Int() # (id, log) je unikatni s indexem
    time = DateTime()
    description = Unicode()
    location_id = Int()
    location = Reference(location_id, Location.id)

class WithHistory(Storm):
    """Base class for evyrything with trackabe history"""

    @property
    def location(self):
        last = self.history.order_by(Desc(History.time)).one()
        if last:
            return last.location
        else:
            return None

class Part(WithHistory):
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
    item_id = Int()
    item = Reference(item_id, "Item.id")
    history_log = Int()
    history = ReferenceSet(history_log, History.log)

class Project(Storm):
    """Model for project"""
    __storm_table__ = "projects"

    id = Int(primary=True)
    name = Unicode(default=u"test")
    summary = Unicode(default=u"pokus")
    description = Unicode()

class Item(WithHistory):
    """Model for actual built items"""
    __storm_table__ = "items"

    id = Int(primary=True)
    kit = Bool() # was this put together as a kit or assembled version?
    description = Unicode()
    parts = ReferenceSet(id, Part.item_id)
    serial = Unicode()
    project_id = Int()
    project = Reference(project_id, Project.id)
    history_log = Int()
    history = ReferenceSet(history_log, History.log)
    
def getStore(url):
    d = create_database(url)
    s = Store(d)
    if url.startswith("sqlite:"):
        s.execute("PRAGMA foreign_keys = ON;")
        
    return s
