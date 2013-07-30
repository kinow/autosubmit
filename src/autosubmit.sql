CREATE TABLE experiment(
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name varchar not null,
	type varchar not null,
	description varchar not null, model_branch varchar, template_name varchar, template_branch varchar, ocean_diagnostics_branch varchar,
	check(length(name) == 4)
);
