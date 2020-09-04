FROM opnfv/functest-kubernetes-core:jerma

ARG CNF_CONFORMANCE_TAG=v0.7.2-beta1

RUN apk --no-cache add --update wget curl libc6-compat && \
    K8S_TAG=$(curl -s https://storage.googleapis.com/kubernetes-release/release/latest-1.19.txt)  && \
    case $(uname -m) in armv7l) ARCH=arm;; aarch64) ARCH=arm64;; x86_64) ARCH=amd64;; esac && \
    curl https://storage.googleapis.com/kubernetes-release/release/$K8S_TAG/bin/linux/$ARCH/kubectl \
        -s --output /usr/local/bin/kubectl && \
    case $(uname -m) in x86_64) \
        curl https://github.com/cncf/cnf-conformance/releases/download/$CNF_CONFORMANCE_TAG/cnf-conformance-$(echo $CNF_CONFORMANCE_TAG |cut -d\- -f 1)-$ARCH-static \
            -Ls --output /usr/local/bin/cnf-conformance && \
            chmod +x /usr/local/bin/cnf-conformance ;; esac && \
    chmod +x /usr/local/bin/kubectl && \
    mkdir -p /src/cnf-conformance && \
    curl -Ls https://raw.githubusercontent.com/cncf/cnf-conformance/$CNF_CONFORMANCE_TAG/example-cnfs/coredns/cnf-conformance.yml \
        -s --output /src/cnf-conformance/cnf-conformance.yml && \
    curl -Ls https://raw.githubusercontent.com/cncf/cnf-conformance/$CNF_CONFORMANCE_TAG/points.yml \
        -s --output /src/cnf-conformance/points.yml
COPY testcases.yaml /usr/lib/python3.7/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
