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
    -e "s|opnfv/functest-kubernetes-core:iruya|\
${repo}/functest-kubernetes-core:amd64-iruya|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:iruya|\
${repo}/functest-kubernetes-healthcheck:amd64-iruya|g" {} +
for dir in ${amd64_dirs}; do
    (cd "${dir}" &&
        docker build "${build_opts[@]}" \
            -t "${repo}/functest-kubernetes-${dir##**/}:amd64-iruya" .)
        docker push "${repo}/functest-kubernetes-${dir##**/}:amd64-iruya"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:amd64-iruya" || true)
done
[ ! -z "${amd64_dirs}" ] &&
    (docker rmi \
        "${repo}/functest-kubernetes-core:amd64-iruya" golang:1.12-alpine3.9 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|golang:1.12-alpine3.9|arm64v8/golang:1.12-alpine3.9|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:iruya|\
${repo}/functest-kubernetes-core:arm64-iruya|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:iruya|\
${repo}/functest-kubernetes-healthcheck:arm64-iruya|g" {} +
for dir in ${arm64_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}:arm64-iruya" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:arm64-iruya"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:arm64-iruya" || true)
done
[ ! -z "${arm64_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-core:arm64-iruya" \
        arm64v8/golang:1.12-alpine3.9 || true)
find . -name Dockerfile -exec git checkout {} +

exit $?
