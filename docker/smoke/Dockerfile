FROM opnfv/functest-kubernetes-healthcheck:jerma

COPY testcases.yaml /usr/lib/python3.7/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
