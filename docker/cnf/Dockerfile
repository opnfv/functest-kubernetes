FROM opnfv/functest-kubernetes-core

ARG CNF_CONFORMANCE_TAG=v0.9.4
ARG HELM_TAG=v3.3.1

RUN apk --no-cache add --update wget curl libc6-compat && \
    K8S_TAG=$(curl -s https://storage.googleapis.com/kubernetes-release/release/latest-1.19.txt)  && \
    case $(uname -m) in armv7l) ARCH=arm;; aarch64) ARCH=arm64;; x86_64) ARCH=amd64;; esac && \
    curl https://storage.googleapis.com/kubernetes-release/release/$K8S_TAG/bin/linux/$ARCH/kubectl \
        -s --output /usr/local/bin/kubectl && \
    curl https://get.helm.sh/helm-$HELM_TAG-linux-$ARCH.tar.gz \
        -s --output /src/helm-$HELM_TAG-linux-$ARCH.tar.gz && \
    tar zxf /src/helm-$HELM_TAG-linux-$ARCH.tar.gz linux-$ARCH/helm -C /src && \
    mv /src/linux-$ARCH/helm /usr/local/bin && \
    chmod +x /usr/local/bin/kubectl /usr/local/bin/helm && \
    rm -r /src/helm-$HELM_TAG-linux-$ARCH.tar.gz /src/linux-$ARCH && \
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
COPY testcases.yaml /usr/lib/python3.8/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
