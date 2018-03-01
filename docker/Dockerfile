FROM alpine:3.7

ARG BRANCH=master
ARG K8S_TAG=v1.7.3
ARG OPENSTACK_TAG=stable/pike

RUN apk --no-cache add --update make py-pip bash git go \
        grep rsync linux-headers musl-dev findutils && \
    git clone https://github.com/kubernetes/kubernetes /src/k8s.io/kubernetes && \
    (cd /src/k8s.io/kubernetes && git checkout $K8S_TAG) && \
    (cd /src/k8s.io/kubernetes && \
        make kubectl ginkgo && \
        make WHAT=test/e2e/e2e.test && \
        mv _output/bin/kubectl /usr/local/bin) && \
    git clone https://gerrit.opnfv.org/gerrit/functest-kubernetes /src/functest-kubernetes && \
    (cd /src/functest-kubernetes && git fetch origin $BRANCH && git checkout FETCH_HEAD) && \
    pip install /src/functest-kubernetes \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt \
        -chttps://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=$OPENSTACK_TAG && \
    rm -rf /src/k8s.io/kubernetes/.git /src/functest-kubernetes && \
    bash -c "mkdir -p /var/lib/xtesting /home/opnfv" && \
    ln -s /var/lib/xtesting /home/opnfv/functest
COPY testcases.yaml /usr/lib/python2.7/site-packages/xtesting/ci/testcases.yaml
COPY logging.ini /usr/lib/python2.7/site-packages/xtesting/ci/logging.ini
CMD ["run_tests", "-t", "all"]
