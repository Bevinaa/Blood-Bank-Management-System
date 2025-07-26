drop table doner;
drop table patient;
drop table bloodbank;

create table doner(
id varchar(50) PRIMARY KEY,
name varchar(30),
gender varchar(8),
dob date,
blood_grp varchar(5),
contact_number number(10),
med_rpt varchar(100),
email varchar(50),
password varchar(50),
age int,
last_donation_date date
);

create table patient(
id varchar(50) PRIMARY KEY,
name varchar(30),
gender varchar(8),
dob date,
blood_grp varchar(5),
contact_number number(10),
med_rpt varchar(100),
email varchar(25),
password varchar(20),
age int,
doner varchar(50)
);

create table bloodbank(
id varchar(50) PRIMARY KEY,
name varchar(50),
director varchar(20),
address varchar(200),
operating_hrs varchar(30),
contact_number int,
email varchar(25),
password varchar(20)
);

