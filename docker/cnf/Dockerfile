FROM opnfv/functest-kubernetes-core

ARG CNF_TESTSUITE_TAG=v1.3.3
ARG HELM_TAG=v3.3.1

USER root
RUN apk --no-cache add --update wget curl ncurses git yaml openssl zlib && \
    apk --no-cache add --virtual .build-deps --update crystal shards make yaml-dev openssl-dev zlib-dev patch openssl-libs-static yaml-static zlib-static && \
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
    (cd /usr/lib/crystal/core/ && \
      wget https://patch-diff.githubusercontent.com/raw/crystal-lang/crystal/pull/13063.diff && \
      patch -p2 < 13063.diff && rm 13063.diff) && \
    case $(uname -m) in x86_64) \
        mkdir /src/cnf-testsuite && \
        git init /src/cnf-testsuite && \
        (cd /src/cnf-testsuite && \
            git fetch --tags https://github.com/cnti-testcatalog/testsuite.git $CNF_TESTSUITE_TAG && \
            git checkout FETCH_HEAD && \
            shards install --without-development && \
            crystal build --static src/cnf-testsuite.cr && \
            cp cnf-testsuite  /usr/local/bin/cnf-testsuite && rm -r lib) && \
        chown -R xtesting: /src/cnf-testsuite && \
        ln -s /src/cnf-testsuite/example-cnfs/coredns/cnf-testsuite.yml /src/cnf-testsuite/cnf-testsuite.yml && \
        ln -s /src/cnf-testsuite/points-all.yml /src/cnf-testsuite/points.yml && \
        rm -rf /src/cnf-testsuite/.git ;; esac && \
        apk del .build-deps
USER xtesting
RUN helm repo add stable https://cncf.gitlab.io/stable
COPY testcases.yaml /etc/xtesting/testcases.yaml
CMD ["run_tests", "-t", "all"]
