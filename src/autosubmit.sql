create table experiment(
	name varchar primary key not null,
	type varchar not null,
	description varchar not null,
	check(length(name) == 4)
);
