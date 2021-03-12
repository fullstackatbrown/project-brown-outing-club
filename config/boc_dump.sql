create table trips
(
	id int auto_increment
		primary key,
	name varchar(120) not null,
	description text null,
	contact varchar(120) null,
	boc_leaders varchar(120) null,
	destination varchar(80) null,
	image text null,
	departure_date date not null,
	departure_location varchar(120) not null,
	departure_time time not null,
	return_date date null,
	return_time time null,
	signup_deadline date not null,
	price decimal(5,2) not null,
	car_cap int null,
	noncar_cap int not null,
	lottery_completed tinyint(1) not null,
	constraint name
		unique (name)
);

create table user
(
	id int auto_increment
		primary key,
	auth_id varchar(80) null,
	email varchar(120) not null,
	weight float not null,
	constraint auth_id
		unique (auth_id),
	constraint email
		unique (email)
);

create table adminclearance
(
	id int auto_increment
		primary key,
	email varchar(120) not null,
	can_create tinyint(1) not null,
	can_edit tinyint(1) not null,
	can_delete tinyint(1) not null,
	constraint adminclearance_ibfk_1
		foreign key (email) references user (email)
			on delete cascade
);

create index email
	on adminclearance (email);

create table responses
(
	id varchar(36) not null
		primary key,
	trip_id int not null,
	user_email varchar(120) not null,
	financial_aid tinyint(1) null,
	car tinyint(1) null,
	lottery_slot tinyint(1) null,
	user_behavior varchar(20) not null,
	constraint responses_ibfk_1
		foreign key (trip_id) references trips (id)
			on delete cascade,
	constraint responses_ibfk_2
		foreign key (user_email) references user (email)
			on delete cascade
);

create index trip_id
	on responses (trip_id);

create index user_email
	on responses (user_email);

create table waitlist
(
	id int auto_increment
		primary key,
	trip_id int not null,
	response_id varchar(36) not null,
	waitlist_rank int not null,
	off tinyint(1) null,
	constraint waitlist_ibfk_1
		foreign key (trip_id) references trips (id)
			on delete cascade,
	constraint waitlist_ibfk_2
		foreign key (response_id) references responses (id)
			on delete cascade
);

create index response_id
	on waitlist (response_id);

create index trip_id
	on waitlist (trip_id);

