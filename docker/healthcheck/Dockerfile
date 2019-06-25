FROM opnfv/functest-kubernetes-core:hunter

ARG K8S_TAG=v1.13.7

RUN apk --no-cache add --update make py-pip bash git \
        grep rsync linux-headers musl-dev findutils \
        libffi openssl libjpeg-turbo && \
    apk --no-cache add --virtual .build-deps --update \
        gcc python-dev libffi-dev openssl-dev libjpeg-turbo-dev && \
    git init /src/k8s.io/kubernetes && \
    (cd /src/k8s.io/kubernetes && \
        git fetch --tags https://github.com/kubernetes/kubernetes $K8S_TAG && \
        git checkout FETCH_HEAD && \
        make kubectl ginkgo && \
        make WHAT=test/e2e/e2e.test && \
        mv _output/bin/* /usr/local/bin) && \
    rm -r /src/k8s.io/kubernetes/.git /src/k8s.io/kubernetes/_output && \
    apk del .build-deps
COPY testcases.yaml /usr/lib/python2.7/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
