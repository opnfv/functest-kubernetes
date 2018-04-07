FROM alpine:3.7

ARG BRANCH=master
ARG OPENSTACK_TAG=stable/pike
ARG OPNFV_TAG=master

RUN apk --no-cache add --update python py-pip bash git grep && \
    git clone https://gerrit.opnfv.org/gerrit/functest-kubernetes /src/functest-kubernetes && \
    (cd /src/functest-kubernetes && git fetch origin $BRANCH && git checkout FETCH_HEAD) && \
    pip install \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$OPNFV_TAG \
        -chttps://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=$OPENSTACK_TAG \
        /src/functest-kubernetes && \
    rm -rf /src/functest-kubernetes && \
    bash -c "mkdir -p /var/lib/xtesting /home/opnfv" && \
    ln -s /var/lib/xtesting /home/opnfv/functest
COPY logging.ini /usr/lib/python2.7/site-packages/xtesting/ci/logging.ini
CMD ["run_tests", "-t", "all"]
