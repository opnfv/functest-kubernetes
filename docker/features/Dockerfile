FROM opnfv/functest-kubernetes-core:gambia

ARG BRANCH=stable/gambia
ARG OPENSTACK_TAG=stable/queens

COPY thirdparty-requirements.txt thirdparty-requirements.txt
RUN apk --no-cache add --update make py-pip bash git go \
        grep rsync linux-headers musl-dev findutils \
        libffi libssl1.0 libjpeg-turbo && \
    apk --no-cache add --virtual .build-deps --update \
        python-dev libffi-dev openssl-dev libjpeg-turbo-dev && \
    pip install \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$BRANCH \
        -chttps://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=$OPENSTACK_TAG \
        -rthirdparty-requirements.txt && \
    rm -f thirdparty-requirements.txt && \
    apk del .build-deps
COPY testcases.yaml /usr/lib/python2.7/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
