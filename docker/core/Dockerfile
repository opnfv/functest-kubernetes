FROM alpine:3.14

ARG BRANCH=stable/v1.22
ARG OPENSTACK_TAG=stable/xena
ARG OPNFV_TAG=stable/v1.22

COPY Try-a-quick-fix-vs-asynchronuous-issues.patch /tmp/Try-a-quick-fix-vs-asynchronuous-issues.patch
COPY Switch-to-threading.Thread-for-Rally-tasks.patch /tmp/Switch-to-threading.Thread-for-Rally-tasks.patch
RUN apk -U upgrade && \
    apk --no-cache add --update python3 py3-pip py3-wheel bash git grep libffi openssl mailcap && \
    apk --no-cache add --virtual .build-deps --update \
        python3-dev build-base libffi-dev openssl-dev rust cargo && \
    git init /src/requirements && \
    (cd /src/requirements && \
        git fetch --tags https://review.opendev.org/openstack/requirements $OPENSTACK_TAG && \
        git checkout FETCH_HEAD) && \
    case $(uname -m) in aarch*|arm*) \
        sed -i -E /^PyNaCl=/d /src/requirements/upper-constraints.txt && \
        apk add --no-cache py3-pynacl ;; esac && \
    sed -i -E /^six=/d /src/requirements/upper-constraints.txt && \
    sed -i -E /^distlib=/d /src/requirements/upper-constraints.txt && \
    sed -i -E /^packaging=/d /src/requirements/upper-constraints.txt && \
    apk --no-cache add --update py3-distlib\>=0.3.1 \
        --repository=http://dl-cdn.alpinelinux.org/alpine/edge/main && \
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
    (cd /usr/lib/python3.9/site-packages/xrally_kubernetes/ && \
        patch -p2 < /tmp/Try-a-quick-fix-vs-asynchronuous-issues.patch) && \
    rm -rf /src/functest-kubernetes /tmp/Switch-to-threading.Thread-for-Rally-tasks.patch && \
    bash -c "mkdir -p /var/lib/xtesting /home/opnfv" && \
    ln -s /var/lib/xtesting /home/opnfv/functest && \
    mkdir -p /etc/rally && \
    printf "[database]\nconnection = 'sqlite:////var/lib/rally/database/rally.sqlite'" > /etc/rally/rally.conf && \
    mkdir -p /var/lib/rally/database && rally db create && \
    rm -r /src/requirements/.git /tmp/Try-a-quick-fix-vs-asynchronuous-issues.patch && \
    apk del .build-deps
COPY logging.ini /usr/lib/python3.9/site-packages/xtesting/ci/logging.ini
COPY logging.debug.ini /usr/lib/python3.9/site-packages/xtesting/ci/logging.debug.ini
CMD ["run_tests", "-t", "all"]
