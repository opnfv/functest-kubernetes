#!/bin/bash

set -e

DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)"
for i in $(cat $DIR/images.txt); do
    sudo docker pull $i
    # https://kind.sigs.k8s.io/docs/user/quick-start/
    # Be free to use docker save && kind load image-archive
    kind load docker-image $i --name latest
done
