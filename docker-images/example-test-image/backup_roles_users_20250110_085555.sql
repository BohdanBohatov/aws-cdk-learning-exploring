--
-- PostgreSQL database cluster dump
--

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE dev_user;
ALTER ROLE dev_user WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS;
CREATE ROLE postgres_admin;
ALTER ROLE postgres_admin WITH NOSUPERUSER INHERIT CREATEROLE CREATEDB LOGIN NOREPLICATION NOBYPASSRLS VALID UNTIL 'infinity';
CREATE ROLE rds_ad;
ALTER ROLE rds_ad WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB NOLOGIN NOREPLICATION NOBYPASSRLS;
CREATE ROLE rds_extension;
ALTER ROLE rds_extension WITH NOSUPERUSER NOINHERIT NOCREATEROLE NOCREATEDB NOLOGIN NOREPLICATION NOBYPASSRLS;
CREATE ROLE rds_iam;
ALTER ROLE rds_iam WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB NOLOGIN NOREPLICATION NOBYPASSRLS;
CREATE ROLE rds_password;
ALTER ROLE rds_password WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB NOLOGIN NOREPLICATION NOBYPASSRLS;
CREATE ROLE rds_replication;
ALTER ROLE rds_replication WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB NOLOGIN NOREPLICATION NOBYPASSRLS;
CREATE ROLE rds_reserved;
ALTER ROLE rds_reserved WITH NOSUPERUSER NOINHERIT NOCREATEROLE NOCREATEDB NOLOGIN NOREPLICATION NOBYPASSRLS;
CREATE ROLE rds_superuser;
ALTER ROLE rds_superuser WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB NOLOGIN NOREPLICATION NOBYPASSRLS;
CREATE ROLE rdsadmin;
ALTER ROLE rdsadmin WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS VALID UNTIL 'infinity';
CREATE ROLE user_1;
ALTER ROLE user_1 WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS;

--
-- User Configurations
--

--
-- User Config "rdsadmin"
--

ALTER ROLE rdsadmin SET "TimeZone" TO 'utc';
ALTER ROLE rdsadmin SET log_statement TO 'all';
ALTER ROLE rdsadmin SET log_min_error_statement TO 'debug5';
ALTER ROLE rdsadmin SET log_min_messages TO 'panic';
ALTER ROLE rdsadmin SET exit_on_error TO '0';
ALTER ROLE rdsadmin SET statement_timeout TO '0';
ALTER ROLE rdsadmin SET role TO 'rdsadmin';
ALTER ROLE rdsadmin SET "auto_explain.log_min_duration" TO '-1';
ALTER ROLE rdsadmin SET temp_file_limit TO '-1';
ALTER ROLE rdsadmin SET search_path TO 'pg_catalog';
ALTER ROLE rdsadmin SET synchronous_commit TO 'local';
ALTER ROLE rdsadmin SET default_tablespace TO '';
ALTER ROLE rdsadmin SET stats_fetch_consistency TO 'snapshot';
ALTER ROLE rdsadmin SET idle_session_timeout TO '0';
ALTER ROLE rdsadmin SET transaction_timeout TO '0';
ALTER ROLE rdsadmin SET event_triggers TO 'on';
ALTER ROLE rdsadmin SET "pg_hint_plan.enable_hint" TO 'off';
ALTER ROLE rdsadmin SET default_transaction_read_only TO 'off';


--
-- Role memberships
--

GRANT pg_checkpoint TO rds_superuser WITH ADMIN OPTION, INHERIT TRUE GRANTED BY rdsadmin;
GRANT pg_create_subscription TO rds_superuser WITH ADMIN OPTION, INHERIT TRUE GRANTED BY rdsadmin;
GRANT pg_maintain TO rds_superuser WITH ADMIN OPTION, INHERIT TRUE GRANTED BY rdsadmin;
GRANT pg_monitor TO rds_superuser WITH ADMIN OPTION, INHERIT TRUE GRANTED BY rdsadmin;
GRANT pg_read_all_data TO rds_superuser WITH ADMIN OPTION, INHERIT TRUE GRANTED BY rdsadmin;
GRANT pg_signal_backend TO rds_superuser WITH ADMIN OPTION, INHERIT TRUE GRANTED BY rdsadmin;
GRANT pg_use_reserved_connections TO rds_superuser WITH ADMIN OPTION, INHERIT TRUE GRANTED BY rdsadmin;
GRANT pg_write_all_data TO rds_superuser WITH ADMIN OPTION, INHERIT TRUE GRANTED BY rdsadmin;
GRANT rds_password TO rds_superuser WITH ADMIN OPTION, INHERIT TRUE GRANTED BY rdsadmin;
GRANT rds_replication TO rds_superuser WITH ADMIN OPTION, INHERIT TRUE GRANTED BY rdsadmin;
GRANT rds_superuser TO postgres_admin WITH INHERIT TRUE GRANTED BY rdsadmin;




--
-- Tablespaces
--

CREATE TABLESPACE rds_temp_tablespace OWNER rds_superuser LOCATION '/rdsdbdata/tmp/rds_temp_tablespace';
GRANT ALL ON TABLESPACE rds_temp_tablespace TO PUBLIC;


--
-- PostgreSQL database cluster dump complete
--

