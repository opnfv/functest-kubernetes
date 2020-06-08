FROM golang:1.12-alpine3.9

ARG BRANCH=stable/iruya
ARG OPENSTACK_TAG=stable/stein
ARG OPNFV_TAG=stable/iruya

RUN apk --no-cache add --update python3 py3-pip bash git grep mailcap && \
    apk --no-cache add --virtual .build-deps --update \
        python3-dev build-base && \
    git init /src/functest-kubernetes && \
    (cd /src/functest-kubernetes && \
        git fetch --tags https://gerrit.opnfv.org/gerrit/functest-kubernetes $BRANCH && \
        git checkout FETCH_HEAD) && \
    pip3 install --no-cache-dir --src /src \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$OPNFV_TAG \
        -chttps://opendev.org/openstack/requirements/raw/branch/$OPENSTACK_TAG/upper-constraints.txt \
        /src/functest-kubernetes && \
    rm -rf /src/functest-kubernetes && \
    bash -c "mkdir -p /var/lib/xtesting /home/opnfv" && \
    ln -s /var/lib/xtesting /home/opnfv/functest && \
    apk del .build-deps
COPY logging.ini /usr/lib/python3.6/site-packages/xtesting/ci/logging.ini
CMD ["run_tests", "-t", "all"]
