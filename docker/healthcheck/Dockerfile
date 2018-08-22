FROM opnfv/functest-kubernetes-core:fraser

ARG K8S_TAG=v1.9.4

RUN apk --no-cache add --update make py-pip bash git go \
        grep rsync linux-headers musl-dev findutils \
        libffi libssl1.0 libjpeg-turbo && \
    apk --no-cache add --virtual .build-deps --update \
        python-dev libffi-dev openssl-dev libjpeg-turbo-dev && \
    git clone https://github.com/kubernetes/kubernetes /src/k8s.io/kubernetes && \
    (cd /src/k8s.io/kubernetes && git checkout $K8S_TAG && \
        # Replace the amd64 with arm64 when building e2e.test on arm platform.
        if [ "`uname -m`" = "aarch64" ]; then sed -i "s/amd64/arm64/g" ./test/images/clusterapi-tester/pod.yaml ; fi && \
        make kubectl ginkgo && \
        make WHAT=test/e2e/e2e.test && \
        mv _output/bin/kubectl /usr/local/bin) && \
    apk del .build-deps
COPY testcases.yaml /usr/lib/python2.7/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
