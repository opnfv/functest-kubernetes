#!/usr/bin/env python

# Copyright (c) 2020 Orange and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

"""Deploy and test Clearwater vIMS using Kubernetes"""

from __future__ import division

import abc
import logging
import time
import subprocess
import re
import yaml

from kubernetes import client
from kubernetes import config
from kubernetes import watch
import pkg_resources

from xtesting.core import testcase


class Vims(testcase.TestCase):  # pylint: disable=too-many-instance-attributes
    """Deploy and test Clearwater vIMS using Kubernetes

    It leverage on the Python kubernetes client to apply operation proposed by
    clearwater-docker.

    See https://github.com/Metaswitch/clearwater-docker for more details
    """
    watch_timeout = 1800
    metadata_name = "env-vars"
    test_image_name = "ollivier/clearwater-live-test:hunter"
    test_container_name = "live-test"
    ns_generate_name = "ims-"

    __logger = logging.getLogger(__name__)

    deployment_list = [
        "astaire", "bono", "cassandra", "chronos", "ellis", "etcd", "homer",
        "homestead", "homestead-prov", "ralf", "sprout"]

    def __init__(self, **kwargs):
        super(Vims, self).__init__(**kwargs)
        config.load_kube_config()
        self.corev1 = client.CoreV1Api()
        self.appsv1 = client.AppsV1Api()
        self.output_log_name = 'functest-kubernetes.log'
        self.output_debug_log_name = 'functest-kubernetes.debug.log'
        self.namespace = ""
        self.zone = ""

    def prepare_vnf(self):
        """Prepare vIMS as proposed by clearwater-live-test

        It creates a dedicated namespace and the configmap needed.

        See https://github.com/Metaswitch/clearwater-live-test for more details
        """
        api_response = self.corev1.create_namespace(
            client.V1Namespace(metadata=client.V1ObjectMeta(
                generate_name=self.ns_generate_name)))
        self.namespace = api_response.metadata.name
        self.__logger.debug("create_namespace: %s", api_response)
        self.zone = '{}.svc.cluster.local'.format(self.namespace)
        metadata = client.V1ObjectMeta(
            name=self.metadata_name, namespace=self.namespace)
        body = client.V1ConfigMap(
            metadata=metadata,
            data={"ADDITIONAL_SHARED_CONFIG": "", "ZONE": self.zone})
        api_response = self.corev1.create_namespaced_config_map(
            self.namespace, body=body)
        self.__logger.debug("create_namespaced_config_map: %s", api_response)

    @abc.abstractmethod
    def deploy_vnf(self):
        """Deploy vIMS as proposed by clearwater-docker

        It must be overriden on purpose.

        See https://github.com/Metaswitch/clearwater-docker for more details
        """

    def wait_vnf(self):
        """Wait vIMS is up and running"""
        assert self.namespace
        status = self.deployment_list.copy()
        watch_deployment = watch.Watch()
        for event in watch_deployment.stream(
                func=self.appsv1.list_namespaced_deployment,
                namespace=self.namespace, timeout_seconds=self.watch_timeout):
            self.__logger.debug(event)
            if event["object"].status.ready_replicas == 1:
                if event['object'].metadata.name in status:
                    status.remove(event['object'].metadata.name)
                    self.__logger.info(
                        "%s started in %0.2f sec",
                        event['object'].metadata.name,
                        time.time()-self.start_time)
            if not status:
                watch_deployment.stop()
        if not status:
            self.result = 1/2 * 100
            return True
        self.__logger.error("Cannot deploy vIMS")
        return False

    def test_vnf(self):
        """Test vIMS as proposed by clearwater-live-test

        It leverages an unofficial Clearwater docker to allow testing from
        the Kubernetes cluster.

        See https://github.com/Metaswitch/clearwater-live-test for more details
        """
        time.sleep(120)
        assert self.namespace
        assert self.zone
        container = client.V1Container(
            name=self.test_container_name, image=self.test_image_name,
            command=["rake", "test[{}]".format(self.zone),
                     "PROXY=bono.{}".format(self.zone),
                     "ELLIS=ellis.{}".format(self.zone),
                     "SIGNUP_CODE=secret", "--trace"])
        spec = client.V1PodSpec(containers=[container], restart_policy="Never")
        metadata = client.V1ObjectMeta(name=self.test_container_name)
        body = client.V1Pod(metadata=metadata, spec=spec)
        api_response = self.corev1.create_namespaced_pod(self.namespace, body)
        watch_deployment = watch.Watch()
        for event in watch_deployment.stream(
                func=self.corev1.list_namespaced_pod,
                namespace=self.namespace, timeout_seconds=self.watch_timeout):
            self.__logger.debug(event)
            if event["object"].metadata.name == self.test_container_name:
                if (event["object"].status.phase == 'Succeeded' or
                        event["object"].status.phase == 'Failed'):
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
            self.prepare_vnf()
            self.deploy_vnf()
            if self.wait_vnf():
                self.test_vnf()
        except client.rest.ApiException:
            self.__logger.exception("Cannot deploy and test vIms")
        self.stop_time = time.time()

    def clean(self):
        try:
            api_response = self.corev1.delete_namespaced_pod(
                name=self.test_container_name, namespace=self.namespace)
            self.__logger.debug("delete_namespaced_pod: %s", api_response)
        except client.rest.ApiException:
            pass
        try:
            api_response = self.corev1.delete_namespaced_config_map(
                name=self.metadata_name, namespace=self.namespace)
            self.__logger.debug(
                "delete_namespaced_config_map: %s", api_response)
        except client.rest.ApiException:
            pass
        try:
            api_response = self.corev1.delete_namespace(self.namespace)
            self.__logger.debug("delete_namespace: %s", self.namespace)
        except client.rest.ApiException:
            pass


class K8sVims(Vims):
    """Deploy vIMS via kubectl as proposed by clearwater-docker

    It leverages unofficial Clearwater dockers as proposed in the
    documentation.

    See https://github.com/Metaswitch/clearwater-docker for more details
    """

    __logger = logging.getLogger(__name__)

    def deploy_vnf(self):
        """Deploy vIMS via kubectl as proposed by clearwater-docker

        See https://github.com/Metaswitch/clearwater-docker for more details
        """
        assert self.namespace
        for deployment in self.deployment_list:
            with open(pkg_resources.resource_filename(
                    'functest_kubernetes',
                    'ims/{}-depl.yaml'.format(deployment))) as yfile:
                body = yaml.safe_load(yfile)
                resp = self.appsv1.create_namespaced_deployment(
                    body=body, namespace=self.namespace)
                self.__logger.info("Deployment %s created", resp.metadata.name)
                self.__logger.debug(
                    "create_namespaced_deployment: %s", resp)
        for service in self.deployment_list:
            with open(pkg_resources.resource_filename(
                    'functest_kubernetes',
                    'ims/{}-svc.yaml'.format(service))) as yfile:
                body = yaml.safe_load(yfile)
                resp = self.corev1.create_namespaced_service(
                    body=body, namespace=self.namespace)
                self.__logger.info("Service %s created", resp.metadata.name)
                self.__logger.debug(
                    "create_namespaced_service: %s", resp)

    def clean(self):
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
        super(K8sVims, self).clean()


class HelmVims(Vims):
    """Deploy vIMS via Helm as proposed by clearwater-docker

    It leverages unofficial Clearwater dockers as proposed in the
    documentation.

    See https://github.com/Metaswitch/clearwater-docker for more details
    """

    __logger = logging.getLogger(__name__)

    def deploy_vnf(self):
        """Deploy vIMS via Helm as proposed by clearwater-docker

        See https://github.com/Metaswitch/clearwater-docker for more details
        """
        cmd = [
            "helm", "install", "clearwater",
            pkg_resources.resource_filename("functest_kubernetes", "ims/helm"),
            "-n", self.namespace]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.debug(output.decode("utf-8"))

    def clean(self):
        cmd = ["helm", "uninstall", "clearwater", "-n", self.namespace]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.debug(output.decode("utf-8"))
        super(HelmVims, self).clean()
