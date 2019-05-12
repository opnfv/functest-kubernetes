FROM opnfv/functest-kubernetes-core

ARG OPENSTACK_TAG=master
ARG OPNFV_TAG=master

COPY thirdparty-requirements.txt thirdparty-requirements.txt
RUN apk --no-cache add --update make bash git go \
        grep rsync linux-headers musl-dev findutils \
        libffi openssl libjpeg-turbo && \
    apk --no-cache add --virtual .build-deps --update \
        python3-dev libffi-dev openssl-dev libjpeg-turbo-dev && \
    pip3 install \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$OPNFV_TAG \
        -chttps://opendev.org/openstack/requirements/raw/branch/$OPENSTACK_TAG/upper-constraints.txt \
        -rthirdparty-requirements.txt && \
    rm -f thirdparty-requirements.txt && \
    apk del .build-deps
COPY testcases.yaml /usr/lib/python3.6/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
