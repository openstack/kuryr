FROM alpine:3.3
MAINTAINER Antoni Segura Puimedon "toni@kuryr.org"
WORKDIR /
RUN apk add --no-cache \
        bash \
        iproute2 \
        openvswitch \
        py-pip \
        python \
        uwsgi-python && \
    apk add --no-cache --virtual build-deps \
        gcc \
        git \
        linux-headers \
        musl-dev \
        python-dev && \
    pip install -U pip setuptools && \
    git clone https://github.com/openstack/kuryr && \
    cd /kuryr && \
    pip install . && \
    cd / && \
    rm -fr /kuryr && \
    apk del build-deps

ENV SERVICE_USER="admin"
ENV SERVICE_TENANT_NAME="admin"
ENV SERVICE_PASSWORD="pass"
ENV IDENTITY_URL="http://127.0.0.1:35357/v2.0"
ENV OS_URL="http://127.0.0.1:9696"
ENV CAPABILITY_SCOPE="local"
ENV LOG_LEVEL="INFO"
ENV PROCESSES=2
ENV THREADS=2

VOLUME /var/log/kuryr

ADD run_kuryr.sh /usr/bin/run_kuryr.sh

CMD ["/usr/bin/run_kuryr.sh"]
