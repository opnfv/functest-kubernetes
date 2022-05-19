FROM opnfv/functest-kubernetes-healthcheck

COPY testcases.yaml /etc/xtesting/testcases.yaml
CMD ["run_tests", "-t", "all"]
