# Functest

Network virtualization has dramatically modified our architectures which asks
for more automation and powerful testing tools like Functest, a collection of
state-of-the-art virtual infrastructure test suites, including automatic VNF
testing (cf.
[[1]](https://www.linuxfoundation.org/press-release/2019/05/opnfv-hunter-delivers-test-tools-ci-cd-framework-to-enable-common-nfvi-for-verifying-vnfs/)).

In context of OPNFV, Functest verifies any kind of OpenStack and Kubernetes
deployments including production environments. It conforms to upstream rules
and integrates smoothly lots of the test cases available in the opensource
market. It includes about 3000+ functional tests and 3 hours upstream API and
dataplane benchmarks. It’s completed by Virtual Network Function deployments
and testing (vIMS, vRouter and vEPC) to ensure that the platforms meet Network
Functions Virtualization requirements. Raspberry PI is also supported to verify
datacenters as the lowest cost (50 euros hardware and software included).

| Functest releases | Kubernetes releases       |
|-------------------|---------------------------|
| Hunter            | v1.13                     |
| **Iruya**         | **v1.15**                 |
| Jerma             | v1.17                     |
| Kali              | v1.19                     |
| Leguer            | v1.20                     |
| Master            | v1.21.0-alpha.3 (rolling) |

## Prepare your environment

cat env
```
DEPLOY_SCENARIO=k8s-XXX
```

## Run healthcheck suite

```bash
sudo docker run --env-file env \
    -v $(pwd)/config:/root/.kube/config \
    opnfv/functest-kubernetes-healthcheck:iruya
```

```
+-------------------+------------------+---------------------+------------------+----------------+
|     TEST CASE     |     PROJECT      |         TIER        |     DURATION     |     RESULT     |
+-------------------+------------------+---------------------+------------------+----------------+
|     k8s_quick     |     functest     |     healthcheck     |      00:14       |      PASS      |
|     k8s_smoke     |     functest     |     healthcheck     |      00:54       |      PASS      |
+-------------------+------------------+---------------------+------------------+----------------+
```

## Run smoke suite

```bash
sudo docker run --env-file env \
    -v $(pwd)/config:/root/.kube/config \
    opnfv/functest-kubernetes-smoke:iruya
```

```
+---------------------------+------------------+---------------+------------------+----------------+
|         TEST CASE         |     PROJECT      |      TIER     |     DURATION     |     RESULT     |
+---------------------------+------------------+---------------+------------------+----------------+
|      k8s_conformance      |     functest     |     smoke     |      94:11       |      PASS      |
|     xrally_kubernetes     |     functest     |     smoke     |      13:39       |      PASS      |
+---------------------------+------------------+---------------+------------------+----------------+
```

## Run security suite

```bash
sudo docker run --env-file env \
    -v $(pwd)/config:/root/.kube/config \
    opnfv/functest-kubernetes-security:iruya
```

```
+---------------------------+------------------+------------------+------------------+----------------+
|         TEST CASE         |     PROJECT      |       TIER       |     DURATION     |     RESULT     |
+---------------------------+------------------+------------------+------------------+----------------+
|        kube_hunter        |     functest     |     security     |      00:21       |      PASS      |
|     kube_bench_master     |     functest     |     security     |      00:01       |      PASS      |
|      kube_bench_node      |     functest     |     security     |      00:01       |      PASS      |
+---------------------------+------------------+------------------+------------------+----------------+
```

## Run benchmarking suite

```bash
sudo docker run --env-file env \
    -v $(pwd)/config:/root/.kube/config \
    opnfv/functest-kubernetes-benchmarking:iruya
```

```
+--------------------------------+------------------+----------------------+------------------+----------------+
|           TEST CASE            |     PROJECT      |         TIER         |     DURATION     |     RESULT     |
+--------------------------------+------------------+----------------------+------------------+----------------+
|     xrally_kubernetes_full     |     functest     |     benchmarking     |      38:21       |      PASS      |
+--------------------------------+------------------+----------------------+------------------+----------------+
```

## Run cnf suite

```bash
sudo docker run --env-file env \
    -v $(pwd)/config:/root/.kube/config \
    opnfv/functest-kubernetes-cnf:iruya
```

```
+-------------------------+------------------+--------------+------------------+----------------+
|        TEST CASE        |     PROJECT      |     TIER     |     DURATION     |     RESULT     |
+-------------------------+------------------+--------------+------------------+----------------+
|         k8s_vims        |     functest     |     cnf      |      08:58       |      PASS      |
|        helm_vims        |     functest     |     cnf      |      08:45       |      PASS      |
|     cnf_conformance     |     functest     |     cnf      |      02:10       |      PASS      |
+-------------------------+------------------+--------------+------------------+----------------+
```
