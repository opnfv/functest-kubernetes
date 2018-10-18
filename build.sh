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
    -e "s|opnfv/functest-kubernetes-core:hunter|\
${repo}/functest-kubernetes-core:amd64-hunter|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:hunter|\
${repo}/functest-kubernetes-healthcheck:amd64-hunter|g" {} +
for dir in ${amd64_dirs}; do
    (cd "${dir}" &&
        docker build "${build_opts[@]}" \
            -t "${repo}/functest-kubernetes-${dir##**/}:amd64-hunter" .)
        docker push "${repo}/functest-kubernetes-${dir##**/}:amd64-hunter"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:amd64-hunter" || true)
done
[ ! -z "${amd64_dirs}" ] &&
    (docker rmi \
        "${repo}/functest-kubernetes-core:amd64-hunter" golang:alpine3.8 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|golang:alpine3.8|arm64v8/golang:alpine3.8|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:hunter|\
${repo}/functest-kubernetes-core:arm64-hunter|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:hunter|\
${repo}/functest-kubernetes-healthcheck:arm64-hunter|g" {} +
for dir in ${arm64_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}:arm64-hunter" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:arm64-hunter"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:arm64-hunter" || true)
done
[ ! -z "${arm64_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-core:arm64-hunter" \
        arm64v8/golang:alpine3.8 || true)
find . -name Dockerfile -exec git checkout {} +

exit $?
