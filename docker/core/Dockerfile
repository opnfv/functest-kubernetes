FROM alpine:3.16

ARG BRANCH=master
ARG OPENSTACK_TAG=master
ARG OPNFV_TAG=master

COPY Try-a-quick-fix-vs-asynchronuous-issues.patch /tmp/Try-a-quick-fix-vs-asynchronuous-issues.patch
COPY Switch-to-threading.Thread-for-Rally-tasks.patch /tmp/Switch-to-threading.Thread-for-Rally-tasks.patch
COPY Enforce-baseline-Pod-Security-Standard-with-namespac.patch /tmp/Enforce-baseline-Pod-Security-Standard-with-namespac.patch
RUN apk -U upgrade && \
    apk --no-cache add --update python3 py3-pip py3-wheel bash git grep libffi openssl mailcap \
        libxml2 libxslt gcompat && \
    ln -sf /lib/libgcompat.so.0 /lib/libresolv.so.2 && \
    apk --no-cache add --virtual .build-deps --update \
        python3-dev build-base libffi-dev openssl-dev rust cargo libxml2-dev libxslt-dev && \
    git init /src/requirements && \
    (cd /src/requirements && \
        git fetch --tags https://review.opendev.org/openstack/requirements $OPENSTACK_TAG && \
        git checkout FETCH_HEAD) && \
    sed -i -E /^packaging==+.*$/d /src/requirements/upper-constraints.txt && \
    sed -i -E /^PyYAML==+.*$/d /src/requirements/upper-constraints.txt && \
    case $(uname -m) in aarch*|arm*) \
        sed -i -E /^PyNaCl=/d /src/requirements/upper-constraints.txt && \
        apk add --no-cache py3-pynacl ;; esac && \
    git init /src/functest-kubernetes && \
    (cd /src/functest-kubernetes && \
        git fetch --tags https://gerrit.opnfv.org/gerrit/functest-kubernetes $BRANCH && \
        git checkout FETCH_HEAD) && \
    pip3 install --use-deprecated=legacy-resolver --no-cache-dir --src /src \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$OPNFV_TAG \
        -c/src/requirements/upper-constraints.txt \
        setuptools_scm && \
    pip3 install --use-deprecated=legacy-resolver --no-cache-dir --src /src \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$OPNFV_TAG \
        -c/src/requirements/upper-constraints.txt \
        /src/functest-kubernetes && \
    (cd /src/rally && patch -p1 < /tmp/Switch-to-threading.Thread-for-Rally-tasks.patch) && \
    (cd /usr/lib/python3.10/site-packages/xrally_kubernetes/ && \
        patch -p2 < /tmp/Try-a-quick-fix-vs-asynchronuous-issues.patch && \
        patch -p2 < /tmp/Enforce-baseline-Pod-Security-Standard-with-namespac.patch) && \
    rm -rf /src/functest-kubernetes /tmp/Switch-to-threading.Thread-for-Rally-tasks.patch && \
    bash -c "mkdir -p /var/lib/xtesting /home/opnfv" && \
    ln -s /var/lib/xtesting /home/opnfv/functest && \
    mkdir -p /etc/rally && \
    printf "[database]\nconnection = 'sqlite:////var/lib/rally/database/rally.sqlite'" > /etc/rally/rally.conf && \
    mkdir -p /var/lib/rally/database && rally db create && \
    rm -r /src/requirements/.git /tmp/Try-a-quick-fix-vs-asynchronuous-issues.patch \
        /tmp/Enforce-baseline-Pod-Security-Standard-with-namespac.patch && \
    addgroup -g 1000 xtesting && adduser -u 1000 -G xtesting -D xtesting && \
    mkdir -p /etc/xtesting && chown -R xtesting: /etc/xtesting /etc/rally && \
    mkdir -p /var/lib/xtesting/results && chown -R xtesting: /var/lib/xtesting /var/lib/rally && \
    apk del .build-deps
USER xtesting
COPY logging.ini /etc/xtesting/logging.ini
COPY logging.debug.ini /etc/xtesting/logging.debug.ini
CMD ["run_tests", "-t", "all"]
