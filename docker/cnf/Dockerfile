FROM opnfv/functest-kubernetes-core:hunter

ARG K8S_TAG=v1.13.12
ARG CNF_CONFORMANCE_TAG=v0.9.4
ARG HELM_TAG=v3.3.1

RUN apk --no-cache add --update wget curl libc6-compat && \
    apk --no-cache add --virtual .build-deps --update make rsync findutils gcc musl-dev && \
    case $(uname -m) in armv7l) ARCH=arm;; aarch64) ARCH=arm64;; x86_64) ARCH=amd64;; esac && \
    git init /src/k8s.io/kubernetes && \
    (cd /src/k8s.io/kubernetes && \
        git fetch --tags https://github.com/kubernetes/kubernetes $K8S_TAG && \
        git checkout FETCH_HEAD && \
        make kubectl && \
        mv _output/bin/* /usr/local/bin) && \
    curl https://get.helm.sh/helm-$HELM_TAG-linux-$ARCH.tar.gz \
        -s --output /src/helm-$HELM_TAG-linux-$ARCH.tar.gz && \
    tar zxf /src/helm-$HELM_TAG-linux-$ARCH.tar.gz linux-$ARCH/helm -C /src && \
    mv /src/linux-$ARCH/helm /usr/local/bin && \
    chmod +x /usr/local/bin/kubectl /usr/local/bin/helm && \
    rm -r /src/k8s.io /src/helm-$HELM_TAG-linux-$ARCH.tar.gz /src/linux-$ARCH && \
    case $(uname -m) in x86_64) \
        curl https://github.com/cncf/cnf-conformance/releases/download/$CNF_CONFORMANCE_TAG/cnf-conformance-$CNF_CONFORMANCE_TAG.tar.gz \
            -Ls --output /src/cnf-conformance-$CNF_CONFORMANCE_TAG.tar.gz && \
        tar zxf /src/cnf-conformance-$CNF_CONFORMANCE_TAG.tar.gz ./cnf-conformance -C /usr/local/bin && \
        chmod +x /usr/local/bin/cnf-conformance && \
        mkdir /src/cnf-conformance && \
        curl -Ls https://raw.githubusercontent.com/cncf/cnf-conformance/e636baff623dd934eadfce77891fc54da08a8134/example-cnfs/coredns/cnf-conformance.yml \
            --output /src/cnf-conformance/cnf-conformance.yml && \
        curl -Ls https://raw.githubusercontent.com/cncf/cnf-conformance/$CNF_CONFORMANCE_TAG/points.yml \
            --output /src/cnf-conformance/points.yml && \
        helm repo add stable https://cncf.gitlab.io/stable && \
        rm /src/cnf-conformance-$CNF_CONFORMANCE_TAG.tar.gz ;; esac
COPY testcases.yaml /usr/lib/python2.7/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
