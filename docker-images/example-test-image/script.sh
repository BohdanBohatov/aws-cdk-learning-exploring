#!/bin/bash
set -e

mkdir -p /var/lib/pgsql/17/dat
chown postgres:postgres /var/lib/pgsql/17/data


su postgres /usr/pgsql-17/bin/initdb -D /var/lib/pgsql/17/data
su postgres echo "listen_addresses='*'" >> /var/lib/pgsql/17/data/postgresql.conf
su postgres echo "host all all 0.0.0.0/0 md5" >> /var/lib/pgsql/17/data/pg_hba.conf
su postgres /usr/pgsql-17/bin/pg_ctl -D /var/lib/pgsql/17/data start

tail -f /dev/null