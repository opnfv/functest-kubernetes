FROM opnfv/functest-kubernetes-core

USER root
RUN apk --no-cache add --update curl libc6-compat && \
    tag=$(curl -Ls https://dl.k8s.io/release/latest.txt)
    case $(uname -m) in armv7l) arch=arm;; aarch64) arch=arm64;; x86_64) arch=amd64;; esac && \
    curl -Ls https://dl.k8s.io/release/$tag/bin/linux/$arch/kubectl \
        --output /usr/local/bin/kubectl && \
    curl -Ls https://dl.k8s.io/release/$tag/kubernetes-test-linux-$arch.tar.gz \
        --output /src/kubernetes-test-linux-$arch.tar.gz && \
    tar zxf /src/kubernetes-test-linux-$arch.tar.gz kubernetes/test/bin/e2e.test kubernetes/test/bin/ginkgo -C /src && \
    mv /src/kubernetes/test/bin/e2e.test /src/kubernetes/test/bin/ginkgo /usr/local/bin/ && \
    chmod +x /usr/local/bin/kubectl /usr/local/bin/e2e.test /usr/local/bin/ginkgo && \
    rm -r /src/kubernetes /src/kubernetes-test-linux-$arch.tar.gz
USER xtesting
COPY testcases.yaml /etc/xtesting/testcases.yaml
CMD ["run_tests", "-t", "all"]
