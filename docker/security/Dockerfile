FROM opnfv/functest-kubernetes-core

ARG OPENSTACK_TAG=master
ARG OPNFV_TAG=master

RUN pip3 install \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$OPNFV_TAG \
        -chttps://opendev.org/openstack/requirements/raw/branch/$OPENSTACK_TAG/upper-constraints.txt \
        git+https://github.com/aquasecurity/kube-hunter.git
COPY testcases.yaml /usr/lib/python3.8/site-packages/xtesting/ci/testcases.yaml
