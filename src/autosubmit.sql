CREATE TABLE experiment(
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name varchar not null,
	type varchar not null,
	description varchar not null,
	check(length(name) == 4)
);
