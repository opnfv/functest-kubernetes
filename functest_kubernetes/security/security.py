#!/usr/bin/env python

# Copyright (c) 2020 Orange and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

"""
Define the parent for Kubernetes testing.
"""

from __future__ import division

import logging
import time
import yaml

from kubernetes import client
from kubernetes import config
from kubernetes import watch
import pkg_resources
from xtesting.core import testcase


class SecurityTesting(testcase.TestCase):
    """Run Security job"""
    namespace = 'default'
    watch_timeout = 1200

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(SecurityTesting, self).__init__(**kwargs)
        config.load_kube_config()
        self.corev1 = client.CoreV1Api()
        self.batchv1 = client.BatchV1Api()
        self.pod = None
        self.job_name = None

    def deploy_job(self):
        """Run Security job

        It runs a single security job and then simply prints its output asis.
        """

        assert self.job_name
        with open(pkg_resources.resource_filename(
                "functest_kubernetes",
                "security/{}.yaml".format(self.job_name))) as yfile:
            body = yaml.safe_load(yfile)
            api_response = self.batchv1.create_namespaced_job(
                body=body, namespace="default")
            self.__logger.info("Job %s created", api_response.metadata.name)
            self.__logger.debug("create_namespaced_job: %s", api_response)
        watch_job = watch.Watch()
        for event in watch_job.stream(
                func=self.batchv1.list_namespaced_job,
                namespace=self.namespace, timeout_seconds=self.watch_timeout):
            if (event["object"].metadata.name == self.job_name and
                    event["object"].status.succeeded == 1):
                self.__logger.info(
                    "%s started in %0.2f sec", event['object'].metadata.name,
                    time.time()-self.start_time)
                watch_job.stop()
        pods = self.corev1.list_namespaced_pod(
            self.namespace, label_selector='job-name={}'.format(self.job_name))
        self.pod = pods.items[0].metadata.name
        api_response = self.corev1.read_namespaced_pod_log(
            name=self.pod, namespace=self.namespace)
        self.__logger.warning("\n\n%s", api_response)
        self.result = 100

    def run(self, **kwargs):
        assert self.job_name
        self.start_time = time.time()
        try:
            self.deploy_job()
        except client.rest.ApiException:
            self.__logger.exception("Cannot run %s", self.job_name)
        self.stop_time = time.time()

    def clean(self):
        try:
            api_response = self.corev1.delete_namespaced_pod(
                name=self.pod, namespace=self.namespace)
            self.__logger.debug("delete_namespaced_pod: %s", api_response)
        except client.rest.ApiException:
            pass
        try:
            api_response = self.batchv1.delete_namespaced_job(
                name=self.job_name, namespace=self.namespace)
            self.__logger.debug(
                "delete_namespaced_deployment: %s", api_response)
        except client.rest.ApiException:
            pass

class KubeHunter(SecurityTesting):
    """kube-hunter hunts for security weaknesses in Kubernetes clusters.

    See https://github.com/aquasecurity/kube-hunter for more details
    """

    def __init__(self, **kwargs):
        super(KubeHunter, self).__init__(**kwargs)
        self.job_name = "kube-hunter"

class KubeBench(SecurityTesting):
    """kube-bench checks whether Kubernetes is deployed securelyself.

    It runs the checks documented in the CIS Kubernetes Benchmark.

    See https://github.com/aquasecurity/kube-bench for more details
    """

    def __init__(self, **kwargs):
        super(KubeBench, self).__init__(**kwargs)
        self.job_name = "kube-bench"
