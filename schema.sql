CREATE TABLE assignments (
       id integer PRIMARY KEY,
       part_type_id integer,
       item_it integer,
       count integer
);

CREATE TABLE items (
       id integer PRIMARY KEY,
       kit boolean default false,
       description varchar,
       serial varchar,
       project_it integer,
       history_log integer
);

CREATE TABLE projects (
       id integer PRIMARY KEY,
       name varchar,
       summary varchar,
       description varchar
);

CREATE TABLE parts (
       id integer PRIMARY KEY,
       count integer,
       source_id integer,
       date datetime,
       price float,
       part_type_id integer,
       assignment_id integer,
       history_log integer,
       manufacturer varchar
);

CREATE TABLE history (
       id integer PRIMARY KEY,
       log integer,
       time datetime,
       description varchar,
       location_id integer
);

CREATE TABLE locations (
       id integer PRIMARY KEY,
       name varchar,
       summary varchar,
       description varchar
);

CREATE TABLE types (
       id integer PRIMARY KEY,
       name varchar,
       summary varchar,
       description varchar,
       pins integer,
       footprint_id integer not null,
       datasheet varchar
);

CREATE TABLE types_sources (
       part_type_id integer,
       source_id integer,
       sku varchar,
       price_id integer
);

CREATE TABLE sources (
       id integer PRIMARY KEY,
       name varchar,
       summary varchar,
       description varchar,
       home varchar,
       url varchar,
       prices varchar,
       customs boolean
);

CREATE TABLE footprints (
       id integer PRIMARY KEY,
       name varchar,
       summary varchar,
       description varchar,
       smd boolean,
       pins integer,
       kicad varchar
);

CREATE TABLE prices (
       id integer PRIMARY KEY,
       time datetime,
       amount integer,
       price float,
       vat_included boolean,
       currency varchar
);

CREATE TABLE tags (
       id integer PRIMARY KEY,
       name varchar,
       summary varchar,
       description varchar
);
