ARG FUNCTION_DIR="/function"

FROM registry.fedoraproject.org/fedora:41

ARG FUNCTION_DIR

RUN mkdir -p ${FUNCTION_DIR}
COPY backup_app.py ${FUNCTION_DIR}

RUN dnf update -y && \
    dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/F-41-x86_64/pgdg-fedora-repo-latest.noarch.rpm && \
    dnf install -y postgresql17 && \
    dnf install -y python3 && \
    dnf install -y python3-pip && \
    pip install --target ${FUNCTION_DIR} awslambdaric && \
    pip install boto3

WORKDIR ${FUNCTION_DIR}

ENTRYPOINT [ "/bin/python", "-m", "awslambdaric" ]

CMD [ "backup_app.lambda_handler" ]