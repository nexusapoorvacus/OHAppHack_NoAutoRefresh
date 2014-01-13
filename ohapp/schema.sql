drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  Name text not null,
  Description text not null,
  Category text not null,
  Username text not null,
  Password text not null,
  Position integer not null
);