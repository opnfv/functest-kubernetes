FROM opnfv/functest-core 

ENV GOROOT=/usr/local/go
ENV PATH=$PATH:$GOROOT/bin

RUN apk --no-cache add --update make bash gcc wget \
    grep rsync linux-headers musl-dev findutils && \
    wget -O go.tgz "http://artifacts.opnfv.org/functest/go.tar.gz" && \
    tar -C /usr/local -xzf go.tgz && \
    git clone https://github.com/kubernetes/kubernetes /src/k8s.io/kubernetes \
    && cd /src/k8s.io/kubernetes && \
    make WHAT=test/e2e/e2e.test
