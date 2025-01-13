ARG FUNCTION_DIR="/function"

FROM registry.fedoraproject.org/fedora:41

ARG FUNCTION_DIR

RUN mkdir -p ${FUNCTION_DIR}
COPY test_app.py ${FUNCTION_DIR}

RUN dnf update -y && \
    dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/F-41-x86_64/pgdg-fedora-repo-latest.noarch.rpm && \
    dnf install -y postgresql17 && \
    dnf install -y postgresql17-contrib && \
    dnf install -y postgresql17-server && \
    dnf install -y python3 && \
    dnf install -y python3-pip && \
    dnf install -y glibc-locale-source glibc-langpack-en && \
    dnf clean all && \
    localedef -i en_US -f UTF-8 en_US.UTF-8 && \
    pip install --target ${FUNCTION_DIR} awslambdaric && \
    pip install boto3

RUN mkdir -p /var/lib/pgsql/17/data && \
    chown postgres:postgres /var/lib/pgsql/17/data && \
    su postgres -c "/usr/pgsql-17/bin/initdb -D /var/lib/pgsql/17/data" && \
    su postgres -c "echo \"listen_addresses='*'\" >> /var/lib/pgsql/17/data/postgresql.conf" && \
    su postgres -c "echo \"host all all 0.0.0.0/0 md5\" >> /var/lib/pgsql/17/data/pg_hba.conf"

WORKDIR ${FUNCTION_DIR}

ENTRYPOINT [ "/bin/python", "-m", "awslambdaric" ]

CMD [ "test_app.lambda_handler" ]