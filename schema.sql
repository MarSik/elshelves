CREATE TABLE meta (
       key varchar PRIMARY KEY,
       value varchar,
       changed timestamp default CURRENT_TIMESTAMP
);

INSERT INTO meta (key, value) VALUES ("version", "0.0.0");

CREATE TABLE sources (
       id integer PRIMARY KEY autoincrement,
       name varchar not null check (length(name)),
       summary varchar,
       description varchar,
       home varchar,
       url varchar,
       prices varchar,
       customs integer
);

CREATE TABLE footprints (
       id integer PRIMARY KEY autoincrement,
       name varchar not null unique check (length(name)),
       summary varchar,
       description varchar,
       smd integer,
       pins integer,
       kicad varchar
);

CREATE INDEX footprints_name on footprints (name);

CREATE TABLE prices (
       id integer PRIMARY KEY autoincrement,
       time datetime,
       amount integer,
       price float,
       vat_included integer,
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
       description varchar
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
       part_type_id integer not null references types (id) on delete restrict on update cascade,
       assignment_id integer references assignments (id) on delete set null on update cascade,
       history_id references history (id) on delete restrict on update cascade,
       soldered integer not null default 0 check ((not usable) or (not soldered) or (assignment_id != NULL)),
       usable integer not null default 1
);


CREATE TABLE types_sources (
       part_type_id integer not null references types (id) on delete cascade on update cascade,
       source_id integer not null references sources (id) on delete cascade on update cascade,
       sku varchar,
       price_id integer references prices (id)
);
