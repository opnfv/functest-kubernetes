FROM opnfv/functest-core

RUN apk --no-cache add --update make bash go \
        grep rsync linux-headers musl-dev findutils && \
    git clone https://github.com/kubernetes/kubernetes /src/k8s.io/kubernetes && \
    cd /src/k8s.io/kubernetes && \
    make WHAT=test/e2e/e2e.test
