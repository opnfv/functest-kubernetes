FROM golang:1.13 AS build
WORKDIR /go/src/github.com/aquasecurity/
RUN git clone https://github.com/aquasecurity/kube-bench.git --depth 1
WORKDIR /go/src/github.com/aquasecurity/kube-bench
RUN GO111MODULE=on CGO_ENABLED=0 go install -a -ldflags "-w"

FROM opnfv/xtesting AS run

ARG K8S_TAG=master
ARG KUBERNETES_VERSION="v1.15.2"
ARG HELM_VERSION="v2.14.1"
ARG OPNFV_TAG=master

# Install kubectl
# Note: Latest version may be found on:
# https://aur.archlinux.org/packages/kubectl-bin/

ADD https://storage.googleapis.com/kubernetes-release/release/${KUBERNETES_VERSION}/bin/linux/amd64/kubectl /usr/local/bin/kubectl

COPY scripts/check_cis_kubernetes.sh /check_cis_kubernetes.sh
COPY --from=build /go/bin/kube-bench /usr/local/bin/kube-bench
COPY --from=build /go/src/github.com/aquasecurity/kube-bench/cfg/ /cfg/

RUN apk --no-cache add --update curl ca-certificates openssl procps util-linux \
        nmap nmap-scripts && \
    apk --no-cache add --virtual .build-deps --update \
        python3-dev linux-headers gcc  musl-dev && \
    git init /src/functest-kubernetes && \
    (cd /src/functest-kubernetes && \
        git fetch --tags https://gerrit.opnfv.org/gerrit/functest-kubernetes $BRANCH && \
        git checkout FETCH_HEAD) && \
    pip3 install \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$OPNFV_TAG \
        -chttps://opendev.org/openstack/requirements/raw/branch/$OPENSTACK_TAG/upper-constraints.txt \
        /src/functest-kubernetes && \
    rm -rf /src/functest-kubernetes && \
    chmod +x /usr/local/bin/kubectl && \
    git clone --depth 1 https://github.com/aquasecurity/kube-hunter.git /kube-hunter && \
    adduser kubectl -Du 2342 -h /config && \
    wget https://storage.googleapis.com/kubernetes-helm/helm-${HELM_VERSION}-linux-amd64.tar.gz -O - | tar -xzO linux-amd64/helm > /usr/local/bin/helm && \
    chmod +x /usr/local/bin/helm && \
    chmod +x /usr/local/bin/kube-bench && \
    chmod +x /check_*.sh && \
    pip3 install -r /kube-hunter/requirements.txt && \
    apk del .build-deps

COPY docker/testcases.yaml /usr/lib/python3.8/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
