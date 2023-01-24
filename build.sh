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
    -e "s|opnfv/functest-kubernetes-core:v1.22|\
${repo}/functest-kubernetes-core:amd64-v1.22|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:v1.22|\
${repo}/functest-kubernetes-healthcheck:amd64-v1.22|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-smoke:v1.22|\
${repo}/functest-kubernetes-smoke:amd64-v1.22|g" {} +
for dir in ${amd64_dirs}; do
    (cd "${dir}" &&
        docker build "${build_opts[@]}" \
            -t "${repo}/functest-kubernetes-${dir##**/}:amd64-v1.22" .)
        docker push "${repo}/functest-kubernetes-${dir##**/}:amd64-v1.22"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:amd64-v1.22" || true)
done
[ ! -z "${amd64_dirs}" ] &&
    (docker rmi \
        "${repo}/functest-kubernetes-core:amd64-v1.22" \
        alpine:3.14 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|alpine:3.14|arm64v8/alpine:3.14|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:v1.22|\
${repo}/functest-kubernetes-core:arm64-v1.22|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:v1.22|\
${repo}/functest-kubernetes-healthcheck:arm64-v1.22|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-smoke:v1.22|\
${repo}/functest-kubernetes-smoke:arm64-v1.22|g" {} +
for dir in ${arm64_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}:arm64-v1.22" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:arm64-v1.22"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:arm64-v1.22" || true)
done
[ ! -z "${arm64_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-core:arm64-v1.22" \
        arm64v8/alpine:3.14 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|alpine:3.14|arm32v7/alpine:3.14|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:v1.22|\
${repo}/functest-kubernetes-core:arm-v1.22|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:v1.22|\
${repo}/functest-kubernetes-healthcheck:arm-v1.22|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-smoke:v1.22|\
${repo}/functest-kubernetes-smoke:arm-v1.22|g" {} +
for dir in ${arm_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}:arm-v1.22" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:arm-v1.22"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:arm-v1.22" || true)
done
[ ! -z "${arm_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-core:arm-v1.22" \
        arm32v7/alpine:3.14 || true)
find . -name Dockerfile -exec git checkout {} +

exit $?
