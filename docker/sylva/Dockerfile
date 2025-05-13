FROM opnfv/functest-kubernetes-core

USER root
RUN apk --no-cache add --update curl && \
    tag=$(curl -Ls https://dl.k8s.io/release/latest.txt) && \
    case $(uname -m) in armv7l) arch=arm;; aarch64) arch=arm64;; x86_64) arch=amd64;; esac && \
    curl -Ls https://dl.k8s.io/release/$tag/bin/linux/$arch/kubectl \
        --output /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl
USER xtesting
COPY testcases.yaml /etc/xtesting/testcases.yaml
WORKDIR /usr/lib/python3.12/site-packages/functest_kubernetes/sylva
CMD ["run_tests", "-t", "all"]
