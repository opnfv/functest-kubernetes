#!/bin/bash

set -e

repo=${REPO:-opnfv}
amd64_dirs=${amd64_dirs-"\
docker/core \
docker/healthcheck \
docker/smoke \
docker/cnf \
docker/security"}
arm_dirs=${arm_dirs-${amd64_dirs}}
arm64_dirs=${arm64_dirs-${amd64_dirs}}
build_opts=(--pull=true --no-cache --force-rm=true)

find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:kali|\
${repo}/functest-kubernetes-core:amd64-kali|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:kali|\
${repo}/functest-kubernetes-healthcheck:amd64-kali|g" {} +
for dir in ${amd64_dirs}; do
    (cd "${dir}" &&
        docker build "${build_opts[@]}" \
            -t "${repo}/functest-kubernetes-${dir##**/}:amd64-kali" .)
        docker push "${repo}/functest-kubernetes-${dir##**/}:amd64-kali"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:amd64-kali" || true)
done
[ ! -z "${amd64_dirs}" ] &&
    (docker rmi \
        "${repo}/functest-kubernetes-core:amd64-kali" \
        golang:1.13-alpine3.11 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|golang:1.13-alpine3.11|arm64v8/golang:1.13-alpine3.11|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:kali|\
${repo}/functest-kubernetes-core:arm64-kali|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:kali|\
${repo}/functest-kubernetes-healthcheck:arm64-kali|g" {} +
for dir in ${arm64_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}:arm64-kali" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:arm64-kali"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:arm64-kali" || true)
done
[ ! -z "${arm64_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-core:arm64-kali" \
        arm64v8/golang:1.13-alpine3.11 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|golang:1.13-alpine3.11|arm32v7/golang:1.13-alpine3.11|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:kali|\
${repo}/functest-kubernetes-core:arm-kali|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:kali|\
${repo}/functest-kubernetes-healthcheck:arm-kali|g" {} +
for dir in ${arm_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}:arm-kali" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:arm-kali"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:arm-kali" || true)
done
[ ! -z "${arm_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-core:arm-kali" \
        arm32v7/golang:1.13-alpine3.11 || true)
find . -name Dockerfile -exec git checkout {} +

exit $?
