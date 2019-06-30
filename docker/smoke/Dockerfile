FROM opnfv/functest-kubernetes-healthcheck

ARG OPENSTACK_TAG=master
ARG RALLY_TAG=master
ARG RALLY_KUBERNETES_TAG=master

RUN apk --no-cache add --update libffi openssl && \
    apk --no-cache add --virtual .build-deps --update \
        python3-dev build-base linux-headers libffi-dev openssl-dev && \
    pip3 install --no-cache-dir --src /src \
        -chttps://opendev.org/openstack/requirements/raw/branch/$OPENSTACK_TAG/upper-constraints.txt \
        -e git+https://opendev.org/openstack/requirements@$OPENSTACK_TAG#egg=openstack_requirements && \
    git init /src/rally && \
    (cd /src/rally && \
        git fetch --tags https://opendev.org/openstack/rally.git $RALLY_TAG && \
        git checkout FETCH_HEAD) && \
    update-requirements -s --source /src/openstack-requirements /src/rally/ && \
    git init /src/xrally-kubernetes && \
    (cd /src/xrally-kubernetes && \
        git fetch --tags https://github.com/xrally/xrally-kubernetes.git $RALLY_KUBERNETES_TAG && \
        git checkout FETCH_HEAD) && \
    pip3 install --no-cache-dir --src /src \
        -chttps://opendev.org/openstack/requirements/raw/branch/$OPENSTACK_TAG/upper-constraints.txt \
        /src/rally /src/xrally-kubernetes && \
    rm -rf /src/rally /src/xrally-kubernetes/.git && \
    mkdir -p /etc/rally && \
    printf "[database]\nconnection = 'sqlite:////var/lib/rally/database/rally.sqlite'" > /etc/rally/rally.conf && \
    mkdir -p /var/lib/rally/database && rally db create && \
    apk del .build-deps

COPY testcases.yaml /usr/lib/python3.6/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
