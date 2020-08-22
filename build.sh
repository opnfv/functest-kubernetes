#!/bin/bash

set -e

repo=${REPO:-opnfv}
amd64_dirs=${amd64_dirs-"\
docker/core \
docker/healthcheck \
docker/smoke \
docker/cnf \
docker/security \
docker/benchmarking"}
arm_dirs=${arm_dirs-${amd64_dirs}}
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
        "${repo}/functest-kubernetes-core:amd64-iruya" \
        alpine:3.9 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|alpine:3.9|arm64v8/alpine:3.9|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:iruya|\
${repo}/functest-kubernetes-core:arm64-iruya|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:iruya|\
${repo}/functest-kubernetes-healthcheck:arm64-iruya|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-smoke:iruya|\
${repo}/functest-kubernetes-smoke:arm64-iruya|g" {} +
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
        arm64v8/alpine:3.9 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|alpine:3.9|arm32v7/alpine:3.9|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:iruya|\
${repo}/functest-kubernetes-core:arm-iruya|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:iruya|\
${repo}/functest-kubernetes-healthcheck:arm-iruya|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-smoke:iruya|\
${repo}/functest-kubernetes-smoke:arm-iruya|g" {} +
for dir in ${arm_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}:arm-iruya" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:arm-iruya"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:arm-iruya" || true)
done
[ ! -z "${arm_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-core:arm-iruya" \
        arm32v7/alpine:3.9 || true)
find . -name Dockerfile -exec git checkout {} +

exit $?
