FROM opnfv/functest-kubernetes-core

ARG K8S_TAG=1.22
ARG CNF_TESTSUITE_TAG=v0.11.0
ARG HELM_TAG=v3.3.1

RUN apk --no-cache add --update wget curl libc6-compat && \
    tag=$(curl -s https://storage.googleapis.com/kubernetes-release/release/latest-$K8S_TAG.txt)  && \
    case $(uname -m) in armv7l) arch=arm;; aarch64) arch=arm64;; x86_64) arch=amd64;; esac && \
    curl https://storage.googleapis.com/kubernetes-release/release/$tag/bin/linux/$arch/kubectl \
        --output /usr/local/bin/kubectl && \
    curl https://get.helm.sh/helm-$HELM_TAG-linux-$arch.tar.gz \
        --output /src/helm-$HELM_TAG-linux-$arch.tar.gz && \
    tar zxf /src/helm-$HELM_TAG-linux-$arch.tar.gz linux-$arch/helm -C /src && \
    mv /src/linux-$arch/helm /usr/local/bin && \
    chmod +x /usr/local/bin/kubectl /usr/local/bin/helm && \
    rm -r /src/helm-$HELM_TAG-linux-$arch.tar.gz /src/linux-$arch && \
    case $(uname -m) in x86_64) \
        curl https://github.com/cncf/cnf-testsuite/releases/download/$CNF_TESTSUITE_TAG/cnf-testsuite-$CNF_TESTSUITE_TAG.tar.gz \
            -L --output /src/cnf-testsuite-$CNF_TESTSUITE_TAG.tar.gz && \
        tar zxf /src/cnf-testsuite-$CNF_TESTSUITE_TAG.tar.gz ./cnf-testsuite -C /usr/local/bin && \
        chmod +x /usr/local/bin/cnf-testsuite && \
        mkdir /src/cnf-testsuite && \
        curl -L https://raw.githubusercontent.com/cncf/cnf-testsuite/$CNF_TESTSUITE_TAG/example-cnfs/coredns/cnf-conformance.yml \
            --output /src/cnf-testsuite/cnf-conformance.yml && \
        curl -L https://raw.githubusercontent.com/cncf/cnf-testsuite/$CNF_TESTSUITE_TAG/points.yml \
            --output /src/cnf-testsuite/points.yml && \
        mkdir -p /src/cnf-testsuite/spec/fixtures && \
        for yml in chaos_network_loss.yml chaos_cpu_hog.yml chaos_container_kill.yml; do \
            curl -L https://raw.githubusercontent.com/cncf/cnf-testsuite/$CNF_TESTSUITE_TAG/spec/fixtures/$yml \
                --output /src/cnf-testsuite/spec/fixtures/$yml; done && \
        helm repo add stable https://cncf.gitlab.io/stable && \
        rm /src/cnf-testsuite-$CNF_TESTSUITE_TAG.tar.gz ;; esac
COPY testcases.yaml /usr/lib/python3.8/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
