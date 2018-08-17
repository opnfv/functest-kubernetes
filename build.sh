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
    -e "s|opnfv/functest-kubernetes-core|${repo}/functest-kubernetes-core|g" \
    {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck|\
${repo}/functest-kubernetes-healthcheck|g" {} +
for dir in ${amd64_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}" .)
    #docker push "${repo}/functest-kubernetes-${dir##**/}"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi "${repo}/functest-kubernetes-${dir##**/}" || true)
done
[ ! -z "${amd64_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-healthcheck" \
        "${repo}/functest-kubernetes-core" alpine:3.7 || true)
find . -name Dockerfile -exec git checkout {} +


#for arm-arch
find . -name Dockerfile -exec sed -i \
    -e "s|alpine:3.7|multiarch/alpine:arm64-v3.7|g" {} +

find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core|${repo}/functest-kubernetes-core|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck|${repo}/functest-kubernetes-healthcheck|g" {} +
for dir in ${arm64_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}" .)
    ## docker push "${repo}/functest-kubernetes-${dir##**/}"

    [ "${dir}" != "docker/core" ] &&
        (docker rmi "${repo}/functest-kubernetes-${dir##**/}" || true)
done
[ ! -z "${arm64_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-healthcheck" \
        "${repo}/functest-kubernetes-core" multiarch/alpine:arm64-v3.7 || true)
find . -name Dockerfile -exec git checkout {} +



exit $?
