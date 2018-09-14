FROM opnfv/functest-kubernetes-core

ARG K8S_TAG=master

RUN apk --no-cache add --update make py-pip bash git \
        grep rsync linux-headers musl-dev findutils \
        libffi libssl1.0 libjpeg-turbo && \
    apk --no-cache add 'go>1.10.2' --repository http://dl-cdn.alpinelinux.org/alpine/edge/community && \
    apk --no-cache add --virtual .build-deps --update \
        python-dev libffi-dev openssl-dev libjpeg-turbo-dev && \
    git init /src/k8s.io/kubernetes && \
    (cd /src/k8s.io/kubernetes && \
        git fetch --tags https://github.com/kubernetes/kubernetes $K8S_TAG && \
        git checkout FETCH_HEAD && \
        # Replace the amd64 with arm64 when building e2e.test on arm platform.
        if [ "$(uname -m)" = "aarch64" ]; then sed -i "s/amd64/arm64/g" ./test/images/clusterapi-tester/pod.yaml ; fi && \
        make kubectl ginkgo && \
        make WHAT=test/e2e/e2e.test && \
        mv _output/bin/* /usr/local/bin) && \
    rm -r /src/k8s.io && \
    apk del .build-deps
COPY testcases.yaml /usr/lib/python2.7/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
