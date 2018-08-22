#!/bin/bash

set -e

repo=${REPO:-opnfv}
amd64_dirs=${amd64_dirs-"\
docker/core \
docker/healthcheck \
docker/smoke \
docker/features"}
arm64_dirs=${arm64_dirs-${amd64_dirs}}
build_opts=(--pull=true --no-cache --force-rm=true)

find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core|\
${repo}/functest-kubernetes-core:amd64-latest|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck|\
${repo}/functest-kubernetes-healthcheck:amd64-latest|g" {} +
for dir in ${amd64_dirs}; do
    (cd "${dir}" &&
        docker build "${build_opts[@]}" \
            -t "${repo}/functest-kubernetes-${dir##**/}:amd64-latest" .)
        docker push "${repo}/functest-kubernetes-${dir##**/}:amd64-latest"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:amd64-latest" || true)
done
[ ! -z "${amd64_dirs}" ] &&
    (docker rmi \
        "${repo}/functest-kubernetes-core:amd64-latest" alpine:3.7 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|alpine:3.7|multiarch/alpine:arm64-v3.7|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core|\
${repo}/functest-kubernetes-core:arm64-latest|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck|\
${repo}/functest-kubernetes-healthcheck:arm64-latest|g" {} +

# When building healthcheck image on arm platform, the "amd64" image version of tester shuold be replaced by "arm64"
[ ! -z "${arm64_dirs}" ] &&
    sed -i '/make kubectl ginkgo/i\sed -i "s/amd64/arm64/g" ./test/images/clusterapi-tester/pod.yaml && \\' docker/healthcheck/Dockerfile

for dir in ${arm64_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}:arm64-latest" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:arm64-latest"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:arm64-latest" || true)
done
[ ! -z "${arm64_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-core:arm64-latest" \
        multiarch/alpine:arm64-v3.7 || true)
find . -name Dockerfile -exec git checkout {} +

exit $?
