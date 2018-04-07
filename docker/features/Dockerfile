FROM opnfv/functest-kubernetes-core

ARG OPENSTACK_TAG=stable/pike
ARG OPNFV_TAG=master

RUN apk --no-cache add --update make py-pip bash git go \
        grep rsync linux-headers musl-dev findutils \
        libffi libssl1.0 libjpeg-turbo && \
    apk --no-cache add --virtual .build-deps --update \
        python-dev libffi-dev openssl-dev libjpeg-turbo-dev && \
    pip install \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$OPNFV_TAG \
        -chttps://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=$OPENSTACK_TAG \
	stor4nfv-tests && \
    apk del .build-deps
COPY testcases.yaml /usr/lib/python2.7/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
