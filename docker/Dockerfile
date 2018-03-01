FROM alpine:3.7

ARG BRANCH=master
ARG K8S_TAG=v1.7.3

RUN apk --no-cache add --update make bash go \
        grep rsync linux-headers musl-dev findutils && \
    git clone https://github.com/kubernetes/kubernetes /src/k8s.io/kubernetes && \
    (cd /src/k8s.io/kubernetes && git checkout $K8S_TAG) && \
    (cd /src/k8s.io/kubernetes && \
        make kubectl ginkgo && \
        make WHAT=test/e2e/e2e.test && \
        mv _output/bin/kubectl /usr/local/bin) && \
    git clone https://gerrit.opnfv.org/gerrit/functest-kubernetes /src/functest-kubernetes && \
    (cd /src/functest-kubernetes && git fetch origin $BRANCH && git checkout FETCH_HEAD) && \
    pip install /src/functest-kubernetes && \
    rm -rf /src/k8s.io/kubernetes/.git /src/functest-kubernetes && \
    ln -s /var/lib/xtesting /home/opnfv/functest
COPY testcases.yaml /usr/lib/python2.7/site-packages/xtesting/ci/testcases.yaml
COPY logging.ini /usr/lib/python2.7/site-packages/xtesting/ci/logging.ini
CMD ["run_tests", "-t", "all"]
