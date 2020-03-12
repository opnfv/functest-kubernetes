#!/usr/bin/env python

# Copyright (c) 2020 Orange and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

"""Deploy and Test Clearwater vIMS using Kubernetes"""

import logging
import time
import re
import yaml

from kubernetes import client
from kubernetes import config
from kubernetes import watch
import pkg_resources

from xtesting.core import testcase


class Vims(testcase.TestCase):
    """Deploy and Test Clearwater vIMS using Kubernetes

    It leverage on the Python kubernetes client to apply operation proposed by
    clearwater-docker.

    See https://github.com/Metaswitch/clearwater-docker for more details
    """
    namespace = 'default'
    zone = 'default.svc.cluster.local'
    watch_timeout = 1200
    metadata_name = "env-vars"
    test_image_name = "ollivier/clearwater-live-test:latest"
    test_container_name = "live-test"

    __logger = logging.getLogger(__name__)

    deployment_list = [
        "astaire", "bono", "cassandra", "chronos", "ellis", "etcd", "homer",
        "homestead", "homestead-prov", "ralf", "sprout"]

    def __init__(self, **kwargs):
        super(Vims, self).__init__(**kwargs)
        config.load_kube_config()
        self.corev1 = client.CoreV1Api()
        self.appsv1 = client.AppsV1Api()

    def deploy_vnf(self):
        """Deploy vIMS as proposed by clearwater-docker

        It leverages on unofficial Clearwater dockers as proposed in the
        documentation.

        See https://github.com/Metaswitch/clearwater-docker for more details
        """
        metadata = client.V1ObjectMeta(
            name=self.metadata_name, namespace=self.namespace)
        body = client.V1ConfigMap(
            metadata=metadata,
            data={"ADDITIONAL_SHARED_CONFIG": "", "ZONE": self.zone})
        api_response = self.corev1.create_namespaced_config_map(
            self.namespace, body=body)
        self.__logger.debug("create_namespaced_config_map: %s", api_response)
        for deployment in self.deployment_list:
            with open(pkg_resources.resource_filename(
                    'functest_kubernetes',
                    'ims/{}-depl.yaml'.format(deployment))) as yfile:
                body = yaml.safe_load(yfile)
                resp = self.appsv1.create_namespaced_deployment(
                    body=body, namespace="default")
                self.__logger.info("Deployment %s created", resp.metadata.name)
                self.__logger.debug(
                    "create_namespaced_deployment: %s", api_response)
        for service in self.deployment_list:
            with open(pkg_resources.resource_filename(
                    'functest_kubernetes',
                    'ims/{}-svc.yaml'.format(service))) as yfile:
                body = yaml.safe_load(yfile)
                resp = self.corev1.create_namespaced_service(
                    body=body, namespace="default")
                self.__logger.info("Service %s created", resp.metadata.name)
                self.__logger.debug(
                    "create_namespaced_service: %s", api_response)
        status = self.deployment_list.copy()
        watch_deployment = watch.Watch()
        for event in watch_deployment.stream(
                func=self.appsv1.list_namespaced_deployment,
                namespace=self.namespace, timeout_seconds=self.watch_timeout):
            if event["object"].status.ready_replicas == 1:
                if event['object'].metadata.name in status:
                    status.remove(event['object'].metadata.name)
                    self.__logger.info(
                        "%s started in %0.2f sec",
                        event['object'].metadata.name,
                        time.time()-self.start_time)
            if len(status) == 0:
                watch_deployment.stop()
        self.result = 1/2 * 100

    def test_vnf(self):
        """Test vIMS as proposed by clearwater-live-test

        It leverages on an unofficial Clearwater docker to allow testing from
        the Kubernetes cluster.

        See https://github.com/Metaswitch/clearwater-live-test for more details
        """
        container = client.V1Container(
            name=self.test_container_name, image=self.test_image_name)
        spec = client.V1PodSpec(containers=[container], restart_policy="Never")
        metadata = client.V1ObjectMeta(name=self.test_container_name)
        body = client.V1Pod(metadata=metadata, spec=spec)
        api_response = self.corev1.create_namespaced_pod(self.namespace, body)
        watch_deployment = watch.Watch()
        for event in watch_deployment.stream(
                func=self.corev1.list_namespaced_pod,
                namespace=self.namespace, timeout_seconds=self.watch_timeout):
            if event["object"].metadata.name == self.test_container_name:
                if (event["object"].status.phase == 'Succeeded'
                        or event["object"].status.phase == 'Error'):
                    watch_deployment.stop()
        api_response = self.corev1.read_namespaced_pod_log(
            name=self.test_container_name, namespace=self.namespace)
        self.__logger.info(api_response)
        vims_test_result = {}
        try:
            grp = re.search(
                r'^(\d+) failures out of (\d+) tests run.*\n'
                r'(\d+) tests skipped$', api_response,
                re.MULTILINE | re.DOTALL)
            assert grp
            vims_test_result["failures"] = int(grp.group(1))
            vims_test_result["total"] = int(grp.group(2))
            vims_test_result["skipped"] = int(grp.group(3))
            vims_test_result['passed'] = (
                int(grp.group(2)) - int(grp.group(3)) - int(grp.group(1)))
            if vims_test_result['total'] - vims_test_result['skipped'] > 0:
                vnf_test_rate = vims_test_result['passed'] / (
                    vims_test_result['total'] - vims_test_result['skipped'])
            else:
                vnf_test_rate = 0
            self.result += 1/2 * 100 * vnf_test_rate
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Cannot parse live tests results")

    def run(self, **kwargs):
        self.start_time = time.time()
        try:
            self.deploy_vnf()
            self.test_vnf()
        except client.rest.ApiException:
            self.__logger.exception("Cannot deploy and test vIms")
        self.stop_time = time.time()

    def clean(self):
        try:
            api_response = self.corev1.delete_namespaced_config_map(
                name=self.metadata_name, namespace=self.namespace)
            self.__logger.debug(
                "delete_namespaced_config_map: %s", api_response)
        except client.rest.ApiException:
            pass
        try:
            api_response = self.corev1.delete_namespaced_pod(
                name=self.test_container_name, namespace=self.namespace)
            self.__logger.debug("delete_namespaced_pod: %s", api_response)
        except client.rest.ApiException:
            pass
        for deployment in self.deployment_list:
            try:
                api_response = self.appsv1.delete_namespaced_deployment(
                    name=deployment, namespace=self.namespace)
                self.__logger.debug(
                    "delete_namespaced_deployment: %s", api_response)
            except client.rest.ApiException:
                pass
            try:
                api_response = self.corev1.delete_namespaced_service(
                    name=deployment, namespace=self.namespace)
                self.__logger.debug(
                    "delete_namespaced_service: %s", api_response)
            except client.rest.ApiException:
                pass
