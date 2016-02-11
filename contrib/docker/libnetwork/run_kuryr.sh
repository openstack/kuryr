#!/bin/bash

mkdir -p /etc/kuryr
cat > /etc/kuryr/kuryr.conf << EOF
[DEFAULT]

bindir = /usr/libexec/kuryr
log_level = $LOG_LEVEL
capability_scope = $CAPABILITY_SCOPE
EOF

/usr/sbin/uwsgi \
    --plugin /usr/lib/uwsgi/python \
    --http-socket :2377 \
    -w kuryr.server:app \
    --master \
    --processes "$PROCESSES" \
    --threads "$THREADS"
