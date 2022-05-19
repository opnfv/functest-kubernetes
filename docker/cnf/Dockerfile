FROM opnfv/functest-kubernetes-core

ARG CNF_TESTSUITE_TAG=v0.15.0
ARG HELM_TAG=v3.3.1

RUN apk --no-cache add --update wget curl libc6-compat ncurses && \
    tag=$(curl -s https://storage.googleapis.com/kubernetes-release/release/latest.txt)  && \
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
        git init /src/cnf-testsuite && \
        (cd /src/cnf-testsuite && \
            git fetch --tags https://github.com/cncf/cnf-testsuite.git $CNF_TESTSUITE_TAG && \
            git checkout FETCH_HEAD) && \
        ln -s /src/cnf-testsuite/example-cnfs/coredns/cnf-testsuite.yml /src/cnf-testsuite/cnf-testsuite.yml && \
        ln -s /src/cnf-testsuite/points-all.yml /src/cnf-testsuite/points.yml && \
        rm -rf /src/cnf-testsuite-$CNF_TESTSUITE_TAG.tar.gz /src/cnf-testsuite/.git ;; esac
COPY testcases.yaml /etc/xtesting/testcases.yaml
CMD ["run_tests", "-t", "all"]
