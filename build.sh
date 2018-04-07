#!/bin/bash

set -e

repo=${REPO:-opnfv}
amd64_dirs=${amd64_dirs-"\
docker/core \
docker/healthcheck \
docker/smoke \
docker/features"}
build_opts=(--pull=true --no-cache --force-rm=true)

find . -name Dockerfile -exec sed -i -e "s|opnfv/functest-kubernetes-core:fraser|${repo}/functest-kubernetes-core:fraser|g" {} +
find . -name Dockerfile -exec sed -i -e "s|opnfv/functest-kubernetes-healthcheck:fraser|${repo}/functest-kubernetes-healthcheck:fraser|g" {} +
for dir in ${amd64_dirs}; do
    (cd "${dir}" && docker build "${build_opts[@]}" -t "${repo}/functest-kubernetes-${dir##**/}:fraser" .)
    docker push "${repo}/functest-kubernetes-${dir##**/}:fraser"
    [ "${dir}" != "docker/core" ] && (docker rmi "${repo}/functest-kubernetes-${dir##**/}:fraser" || true)
done
[ ! -z "${amd64_dirs}" ] && (docker rmi "${repo}/functest-kubernetes-core:fraser" alpine:3.7 || true)
find . -name Dockerfile -exec git checkout {} +

exit $?
