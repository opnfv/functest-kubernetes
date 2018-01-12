FROM opnfv/functest-core

ARG K8S_TAG=v1.9.1

RUN apk --no-cache add --update make bash go \
        grep rsync linux-headers musl-dev findutils && \
    git clone https://github.com/kubernetes/kubernetes /src/k8s.io/kubernetes && \
    (cd /src/k8s.io/kubernetes && git checkout $K8S_TAG) && \
    (cd /src/k8s.io/kubernetes && make WHAT=test/e2e/e2e.test) && \
    rm -rf /src/k8s.io/kubernetes/.git
