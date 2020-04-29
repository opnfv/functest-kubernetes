FROM golang:1.13-alpine3.11

ARG BRANCH=stable/kali
ARG OPENSTACK_TAG=master
ARG OPNFV_TAG=stable/kali

RUN apk --no-cache add --update python3 bash git grep libffi openssl mailcap && \
    apk --no-cache add --virtual .build-deps --update \
        python3-dev build-base libffi-dev openssl-dev && \
    git init /src/functest-kubernetes && \
    (cd /src/functest-kubernetes && \
        git fetch --tags https://gerrit.opnfv.org/gerrit/functest-kubernetes $BRANCH && \
        git checkout FETCH_HEAD) && \
    pip3 install \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$OPNFV_TAG \
        -chttps://opendev.org/openstack/requirements/raw/branch/$OPENSTACK_TAG/upper-constraints.txt \
        /src/functest-kubernetes && \
    rm -rf /src/functest-kubernetes && \
    bash -c "mkdir -p /var/lib/xtesting /home/opnfv" && \
    ln -s /var/lib/xtesting /home/opnfv/functest && \
    mkdir -p /etc/rally && \
    printf "[database]\nconnection = 'sqlite:////var/lib/rally/database/rally.sqlite'" > /etc/rally/rally.conf && \
    mkdir -p /var/lib/rally/database && rally db create && \
    apk del .build-deps
COPY logging.ini /usr/lib/python3.8/site-packages/xtesting/ci/logging.ini
COPY logging.debug.ini /usr/lib/python3.8/site-packages/xtesting/ci/logging.debug.ini
CMD ["run_tests", "-t", "all"]
