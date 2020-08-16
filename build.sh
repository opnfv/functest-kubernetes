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
    -e "s|opnfv/functest-kubernetes-core:jerma|\
${repo}/functest-kubernetes-core:amd64-jerma|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:jerma|\
${repo}/functest-kubernetes-healthcheck:amd64-jerma|g" {} +
for dir in ${amd64_dirs}; do
    (cd "${dir}" &&
        docker build "${build_opts[@]}" \
            -t "${repo}/functest-kubernetes-${dir##**/}:amd64-jerma" .)
        docker push "${repo}/functest-kubernetes-${dir##**/}:amd64-jerma"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:amd64-jerma" || true)
done
[ ! -z "${amd64_dirs}" ] &&
    (docker rmi \
        "${repo}/functest-kubernetes-core:amd64-jerma" \
        alpine:3.10 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|alpine:3.10|arm64v8/alpine:3.10|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:jerma|\
${repo}/functest-kubernetes-core:arm64-jerma|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:jerma|\
${repo}/functest-kubernetes-healthcheck:arm64-jerma|g" {} +
for dir in ${arm64_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}:arm64-jerma" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:arm64-jerma"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:arm64-jerma" || true)
done
[ ! -z "${arm64_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-core:arm64-jerma" \
        arm64v8/alpine:3.10 || true)
find . -name Dockerfile -exec git checkout {} +

find . -name Dockerfile -exec sed -i \
    -e "s|alpine:3.10|arm32v7/alpine:3.10|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-core:jerma|\
${repo}/functest-kubernetes-core:arm-jerma|g" {} +
find . -name Dockerfile -exec sed -i \
    -e "s|opnfv/functest-kubernetes-healthcheck:jerma|\
${repo}/functest-kubernetes-healthcheck:arm-jerma|g" {} +
for dir in ${arm_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" \
        -t "${repo}/functest-kubernetes-${dir##**/}:arm-jerma" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:arm-jerma"
    [ "${dir}" != "docker/core" ] &&
        (docker rmi \
            "${repo}/functest-kubernetes-${dir##**/}:arm-jerma" || true)
done
[ ! -z "${arm_dirs}" ] &&
    (docker rmi "${repo}/functest-kubernetes-core:arm-jerma" \
        arm32v7/alpine:3.10 || true)
find . -name Dockerfile -exec git checkout {} +

exit $?
