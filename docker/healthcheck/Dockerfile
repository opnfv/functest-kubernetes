FROM opnfv/functest-kubernetes-core:kali

RUN apk --no-cache add --update curl libc6-compat && \
    K8S_TAG=$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable-1.19.txt)  && \
    case $(uname -m) in armv7l) ARCH=arm;; aarch64) ARCH=arm64;; x86_64) ARCH=amd64;; esac && \
    curl https://storage.googleapis.com/kubernetes-release/release/$K8S_TAG/bin/linux/$ARCH/kubectl \
        -s --output /usr/local/bin/kubectl && \
    curl https://storage.googleapis.com/kubernetes-release/release/$K8S_TAG/kubernetes-test-linux-$ARCH.tar.gz \
        -s --output /src/kubernetes-test-linux-$ARCH.tar.gz && \
    tar zxf /src/kubernetes-test-linux-$ARCH.tar.gz kubernetes/test/bin/e2e.test kubernetes/test/bin/ginkgo -C /src && \
    mv /src/kubernetes/test/bin/e2e.test /src/kubernetes/test/bin/ginkgo /usr/local/bin/ && \
    chmod +x /usr/local/bin/kubectl /usr/local/bin/e2e.test /usr/local/bin/ginkgo && \
    rm -r /src/kubernetes /src/kubernetes-test-linux-$ARCH.tar.gz
COPY testcases.yaml /usr/lib/python3.8/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
