FROM opnfv/functest-kubernetes-core:hunter

ARG K8S_TAG=v1.13.12
ARG CNF_CONFORMANCE_TAG=v0.7.2-beta1

RUN apk --no-cache add --update wget curl libc6-compat && \
    apk --no-cache add --virtual .build-deps --update make rsync findutils gcc musl-dev && \
    case $(uname -m) in armv7l) ARCH=arm;; aarch64) ARCH=arm64;; x86_64) ARCH=amd64;; esac && \
    git init /src/k8s.io/kubernetes && \
    (cd /src/k8s.io/kubernetes && \
        git fetch --tags https://github.com/kubernetes/kubernetes $K8S_TAG && \
        git checkout FETCH_HEAD && \
        make kubectl && \
        mv _output/bin/* /usr/local/bin) && \
    rm -r /src/k8s.io && \
    case $(uname -m) in x86_64) \
        curl https://github.com/cncf/cnf-conformance/releases/download/$CNF_CONFORMANCE_TAG/cnf-conformance-$(echo $CNF_CONFORMANCE_TAG |cut -d\- -f 1)-$ARCH-static \
            -Ls --output /usr/local/bin/cnf-conformance && \
            chmod +x /usr/local/bin/cnf-conformance ;; esac && \
    mkdir -p /src/cnf-conformance && \
    curl -Ls https://raw.githubusercontent.com/cncf/cnf-conformance/$CNF_CONFORMANCE_TAG/example-cnfs/coredns/cnf-conformance.yml \
        -s --output /src/cnf-conformance/cnf-conformance.yml && \
    curl -Ls https://raw.githubusercontent.com/cncf/cnf-conformance/$CNF_CONFORMANCE_TAG/points.yml \
        -s --output /src/cnf-conformance/points.yml && \
    apk del .build-deps
COPY testcases.yaml /usr/lib/python2.7/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
