FROM opnfv/functest-kubernetes-smoke:kali

ARG OPENSTACK_TAG=stable/ussuri
ARG OPNFV_TAG=stable/kali
ARG NETPERF_TAG=8a5a7a23f2165b29e46b4d32aad7d5f85e4b9516
ARG PLOTPERF_TAG=2455313f4b9581795a8f642243acaad472d91804

COPY plotperf.py.patch /tmp/plotperf.py.patch
RUN apk --no-cache add py3-numpy freetype libstdc++ --update && \
    apk --no-cache add --virtual .build-deps --update patch go python3-dev build-base freetype-dev && \
    pip3 install --use-deprecated=legacy-resolver --no-cache-dir --src /src \
        -chttps://git.opnfv.org/functest/plain/upper-constraints.txt?h=$OPNFV_TAG \
        -chttps://opendev.org/openstack/requirements/raw/branch/$OPENSTACK_TAG/upper-constraints.txt \
        matplotlib===3.1.3 kiwisolver===1.1.0 cycler===0.10.0 && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    git clone https://github.com/kubernetes/perf-tests && \
    (cd perf-tests && git checkout $NETPERF_TAG) && \
    (cd perf-tests/network/benchmarks/netperf && go build -o /usr/local/bin/launch launch.go) && \
    curl https://raw.githubusercontent.com/girishkalele/pyplot-docker/$PLOTPERF_TAG/plotperf.py \
        --output /usr/local/bin/plotperf.py && \
    (cd /usr/local/bin && patch -p0 < /tmp/plotperf.py.patch && \
        mv plotperf.py plotperf && chmod a+x plotperf) && \
    rm -rf perf-tests /tmp/plotperf.py.patch && \
    apk del .build-deps
COPY testcases.yaml /usr/lib/python3.8/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
