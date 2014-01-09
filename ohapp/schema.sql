drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  Name text not null,
  Description text not null,
  Category text not null
);