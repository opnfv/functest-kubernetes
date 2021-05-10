FROM opnfv/functest-kubernetes-smoke

ARG NETPERF_TAG=master
ARG PLOTPERF_TAG=master

COPY plotperf.py.patch /tmp/plotperf.py.patch
RUN apk --no-cache add --update py3-matplotlib && \
    apk --no-cache add --virtual .build-deps --update patch go && \
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
