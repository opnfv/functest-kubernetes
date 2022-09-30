FROM opnfv/functest-kubernetes-core:v1.25

ARG K8S_TAG=1.25
RUN apk --no-cache add --update curl libc6-compat && \
    tag=$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable-$K8S_TAG.txt)  && \
    case $(uname -m) in armv7l) arch=arm;; aarch64) arch=arm64;; x86_64) arch=amd64;; esac && \
    curl https://storage.googleapis.com/kubernetes-release/release/$tag/bin/linux/$arch/kubectl \
        -s --output /usr/local/bin/kubectl && \
    curl https://storage.googleapis.com/kubernetes-release/release/$tag/kubernetes-test-linux-$arch.tar.gz \
        -s --output /src/kubernetes-test-linux-$arch.tar.gz && \
    tar zxf /src/kubernetes-test-linux-$arch.tar.gz kubernetes/test/bin/e2e.test kubernetes/test/bin/ginkgo -C /src && \
    mv /src/kubernetes/test/bin/e2e.test /src/kubernetes/test/bin/ginkgo /usr/local/bin/ && \
    chmod +x /usr/local/bin/kubectl /usr/local/bin/e2e.test /usr/local/bin/ginkgo && \
    rm -r /src/kubernetes /src/kubernetes-test-linux-$arch.tar.gz
COPY testcases.yaml /etc/xtesting/testcases.yaml
CMD ["run_tests", "-t", "all"]
