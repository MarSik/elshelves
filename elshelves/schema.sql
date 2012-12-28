PRAGMA foreign_keys=ON;

CREATE TABLE meta (
       key varchar PRIMARY KEY,
       value varchar,
       changed timestamp default CURRENT_TIMESTAMP
);

INSERT INTO meta (key, value) VALUES ("version", "0.1.0");

CREATE TABLE sources (
       id integer PRIMARY KEY autoincrement,
       name varchar not null check (length(name)),
       summary varchar,
       description varchar,
       home varchar,
       vat float,
       url varchar,
       prices varchar,
       customs integer
);

CREATE TABLE footprints (
       id integer PRIMARY KEY autoincrement,
       name varchar not null unique check (length(name)),
       summary varchar,
       description varchar,
       pins integer,
       holes integer,
       kicad varchar
);

CREATE INDEX footprints_name on footprints (name);

CREATE TABLE prices (
       id integer PRIMARY KEY autoincrement,
       time datetime,
       amount integer,
       price float,
       vat float,
       currency varchar
);

CREATE TABLE tags (
       id integer PRIMARY KEY autoincrement,
       name varchar unique not null check (length(name)),
       summary varchar,
       description varchar
);

CREATE TABLE locations (
       id integer PRIMARY KEY autoincrement,
       name varchar not null check (length(name)),
       summary varchar,
       description varchar
);

CREATE TABLE history (
       id integer PRIMARY KEY autoincrement,
       parent_id integer references history (id) on delete restrict on update cascade,
       time datetime not null default CURRENT_TIMESTAMP,
       event int,
       description varchar,
       location_id integer references locations (id) on delete restrict on update cascade
);

CREATE INDEX history_parent on history (parent_id);


CREATE TABLE projects (
       id integer PRIMARY KEY autoincrement,
       name varchar not null check (length(name)),
       summary varchar,
       description varchar,
       started datetime not null default CURRENT_DATE
);

CREATE TABLE items (
       id integer PRIMARY KEY autoincrement,
       kit integer default 0,
       description varchar,
       serial varchar not null,
       project_id integer not null references projects (id) on delete restrict on update cascade,
       history_id integer references history (id) on delete restrict on update cascade
);

CREATE UNIQUE INDEX items_serial on items (project_id, serial);

CREATE TABLE types (
       id integer PRIMARY KEY autoincrement,
       name varchar not null check (length(name)),
       summary varchar,
       description varchar,
       pins integer,
       footprint_id integer not null references footprints (id) on delete restrict on update cascade,
       datasheet varchar,
       manufacturer varchar
);

CREATE TABLE terms_types (
       term_id integer not null references terms (id) on delete cascade on update cascade,
       type_id integer not null references types (id) on delete cascade on update cascade
);

CREATE INDEX term_mapping on terms_types (term_id);

CREATE UNIQUE INDEX term_type_mapping on terms_types (term_id, type_id);

CREATE TABLE terms (
       id integer not null PRIMARY KEY autoincrement,
       term varchar not null UNIQUE check (length(term)),
       alias_for_id integer references terms (id) on delete restrict on update cascade
);

CREATE TABLE assignments (
       id integer PRIMARY KEY autoincrement,
       part_type_id integer not null references types (id) on delete cascade on update cascade,
       item_id integer not null references items (id) on delete cascade on update cascade,
       count integer not null
);

CREATE TABLE parts (
       id integer PRIMARY KEY autoincrement,
       count integer not null check (count > 0),
       source_id integer references sources (id) on delete restrict on update cascade,
       date datetime not null default CURRENT_DATE,
       price float,
       vat float,
       part_type_id integer not null references types (id) on delete restrict on update cascade,
       assignment_id integer references assignments (id) on delete set null on update cascade,
       history_id references history (id) on delete restrict on update cascade,
       soldered integer not null default 0 check ((not usable) or (usable and not soldered) or (usable and assignment_id != NULL)),
       usable integer not null default 1
);

CREATE INDEX parts_buys on parts (date, source_id);

CREATE TRIGGER parts_update AFTER UPDATE OF assignment_id ON parts WHEN new.assignment_id != NULL BEGIN
INSERT INTO history (parent_id,event,description) VALUES (new.history_id, 3, "_added to project");
UPDATE parts SET history_id = rowid WHERE id = new.id;
END;

CREATE TRIGGER parts_remove AFTER UPDATE OF assignment_id ON parts WHEN new.assignment_id == NULL BEGIN
INSERT INTO history (parent_id,event,description) VALUES (new.history_id, 3, "_removed from project");
UPDATE parts SET history_id = rowid WHERE id = new.id;
END;

CREATE TRIGGER parts_solder AFTER UPDATE OF soldered ON parts WHEN new.soldered == 1 and old.soldered == 0 BEGIN
INSERT INTO history (parent_id,event,description) VALUES (new.history_id, 4, "_soldered to board");
UPDATE parts SET history_id = rowid WHERE id = new.id;
END;

CREATE TRIGGER parts_unsolder AFTER UPDATE OF soldered ON parts WHEN new.soldered == 0 and old.soldered == 1 BEGIN
INSERT INTO history (parent_id,event,description) VALUES (new.history_id, 3, "_unsoldered from board");
UPDATE parts SET history_id = rowid WHERE id = new.id;
END;

CREATE TRIGGER parts_destroy AFTER UPDATE OF usable ON parts WHEN new.usable == 0 and old.usable == 1 BEGIN
INSERT INTO history (parent_id,event,description) VALUES (new.history_id, 5, "_destroyed");
UPDATE parts SET history_id = rowid WHERE id = new.id;
END;

CREATE TRIGGER parts_revive AFTER UPDATE OF usable ON parts WHEN new.usable > 0 and old.usable == 0 BEGIN
INSERT INTO history (parent_id,event,description) VALUES (new.history_id, 3, "_repaired");
UPDATE parts SET history_id = rowid WHERE id = new.id;
END;


CREATE TABLE types_sources (
       part_type_id integer not null references types (id) on delete cascade on update cascade,
       source_id integer not null references sources (id) on delete cascade on update cascade,
       sku varchar,
       price_id integer references prices (id)
);
