FROM opnfv/functest-kubernetes-healthcheck:v1.32

COPY testcases.yaml /etc/xtesting/testcases.yaml
CMD ["run_tests", "-t", "all"]
