#!/bin/bash

set -e

tmpfile=$(mktemp)
cat << EOF > $tmpfile
docker.io/appropriate/curl:edge
docker.io/aquasec/kube-bench:0.3.1
docker.io/aquasec/kube-hunter:0.3.1
docker.io/gluster/glusterdynamic-provisioner:v1.0
docker.io/library/busybox:1.28
docker.io/library/busybox:1.29
docker.io/library/httpd:2.4.38-alpine
docker.io/library/httpd:2.4.39-alpine
docker.io/library/nginx:1.14-alpine
docker.io/library/nginx:1.15-alpine
docker.io/library/perl:5.26
docker.io/library/redis:5.0.5-alpine
docker.io/ollivier/clearwater-astaire:hunter
docker.io/ollivier/clearwater-bono:hunter
docker.io/ollivier/clearwater-cassandra:hunter
docker.io/ollivier/clearwater-chronos:hunter
docker.io/ollivier/clearwater-ellis:hunter
docker.io/ollivier/clearwater-homer:hunter
docker.io/ollivier/clearwater-homestead:hunter
docker.io/ollivier/clearwater-homestead-prov:hunter
docker.io/ollivier/clearwater-live-test:hunter
docker.io/ollivier/clearwater-ralf:hunter
docker.io/ollivier/clearwater-sprout:hunter
gcr.io/google-samples/hello-go-gke:1.0
gcr.io/kubernetes-e2e-test-images/apparmor-loader:1.0
gcr.io/kubernetes-e2e-test-images/cuda-vector-add:1.0
gcr.io/kubernetes-e2e-test-images/cuda-vector-add:2.0
gcr.io/kubernetes-e2e-test-images/echoserver:2.2
gcr.io/kubernetes-e2e-test-images/ipc-utils:1.0
gcr.io/kubernetes-e2e-test-images/jessie-dnsutils:1.0
gcr.io/kubernetes-e2e-test-images/kitten:1.0
gcr.io/kubernetes-e2e-test-images/metadata-concealment:1.2
gcr.io/kubernetes-e2e-test-images/nautilus:1.0
gcr.io/kubernetes-e2e-test-images/nonewprivs:1.0
gcr.io/kubernetes-e2e-test-images/nonroot:1.0
gcr.io/kubernetes-e2e-test-images/regression-issue-74839-amd64:1.0
gcr.io/kubernetes-e2e-test-images/resource-consumer:1.5
gcr.io/kubernetes-e2e-test-images/sample-apiserver:1.17
gcr.io/kubernetes-e2e-test-images/volume/gluster:1.0
gcr.io/kubernetes-e2e-test-images/volume/iscsi:2.0
gcr.io/kubernetes-e2e-test-images/volume/nfs:1.0
gcr.io/kubernetes-e2e-test-images/volume/rbd:1.0.1
k8s.gcr.io/build-image/debian-iptables:v12.1.2
k8s.gcr.io/conformance:v1.19.0
k8s.gcr.io/e2e-test-images/agnhost:2.20
k8s.gcr.io/etcd:3.4.9
k8s.gcr.io/pause:3.2
k8s.gcr.io/pause:3.3
k8s.gcr.io/prometheus-dummy-exporter:v0.1.0
k8s.gcr.io/prometheus-to-sd:v0.5.0
k8s.gcr.io/sd-dummy-exporter:v0.2.0
k8s.gcr.io/sig-storage/nfs-provisioner:v2.2.2
quay.io/coreos/etcd:v2.2.5
EOF
for i in $(cat $tmpfile); do
    sudo docker pull $i
    # https://kind.sigs.k8s.io/docs/user/quick-start/
    # Be free to use docker save && kind load image-archive
    kind load docker-image $i --name latest
done
rm -f $tmpfile
