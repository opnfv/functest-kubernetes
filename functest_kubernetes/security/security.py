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

import ast
import json
import logging
import os
import time
import textwrap
import yaml

from jinja2 import Template
from kubernetes import client
from kubernetes import config
from kubernetes import watch
import pkg_resources
import prettytable

from xtesting.core import testcase


class SecurityTesting(testcase.TestCase):
    # pylint: disable=too-many-instance-attributes
    """Run Security job"""
    watch_timeout = 1200
    dockerhub_repo = os.getenv("MIRROR_REPO", "docker.io")

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config.load_kube_config()
        self.corev1 = client.CoreV1Api()
        self.batchv1 = client.BatchV1Api()
        self.pod = None
        self.pod_log = ""
        self.job_name = None
        self.output_log_name = 'functest-kubernetes.log'
        self.output_debug_log_name = 'functest-kubernetes.debug.log'
        self.namespace = ""
        self.ns_generate_name = "security-"

    def deploy_job(self):
        """Run Security job

        It runs a single security job and then simply prints its output asis.
        """

        assert self.job_name
        api_response = self.corev1.create_namespace(
            client.V1Namespace(metadata=client.V1ObjectMeta(
                generate_name=self.ns_generate_name,
                labels={"pod-security.kubernetes.io/enforce": "baseline"})))
        self.namespace = api_response.metadata.name
        self.__logger.debug("create_namespace: %s", api_response)
        with open(pkg_resources.resource_filename(
                "functest_kubernetes",
                f"security/{self.job_name}.yaml"),
                encoding='utf-8') as yfile:
            template = Template(yfile.read())
            body = yaml.safe_load(template.render(
                dockerhub_repo=os.getenv("DOCKERHUB_REPO",
                                         self.dockerhub_repo)))
            api_response = self.batchv1.create_namespaced_job(
                body=body, namespace=self.namespace)
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
            self.namespace, label_selector=f'job-name={self.job_name}')
        self.pod = pods.items[0].metadata.name
        self.pod_log = self.corev1.read_namespaced_pod_log(
            name=self.pod, namespace=self.namespace)
        self.__logger.info("\n\n%s", self.pod_log)

    def run(self, **kwargs):
        assert self.job_name
        self.start_time = time.time()
        try:
            self.deploy_job()
        except client.rest.ApiException:
            self.__logger.exception("Cannot run %s", self.job_name)
        self.stop_time = time.time()

    def clean(self):
        if self.pod:
            try:
                api_response = self.corev1.delete_namespaced_pod(
                    name=self.pod, namespace=self.namespace)
                self.__logger.debug("delete_namespaced_pod: %s", api_response)
            except client.rest.ApiException:
                pass
        if self.job_name:
            try:
                api_response = self.batchv1.delete_namespaced_job(
                    name=self.job_name, namespace=self.namespace)
                self.__logger.debug(
                    "delete_namespaced_deployment: %s", api_response)
            except client.rest.ApiException:
                pass
        if self.namespace:
            try:
                api_response = self.corev1.delete_namespace(self.namespace)
                self.__logger.debug("delete_namespace: %s", self.namespace)
            except client.rest.ApiException:
                pass


class KubeHunter(SecurityTesting):
    """kube-hunter hunts for security weaknesses in Kubernetes clusters.

    See https://github.com/aquasecurity/kube-hunter for more details
    """

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.job_name = "kube-hunter"
        self.ns_generate_name = "kube-hunter-"

    def process_results(self, **kwargs):
        """Process kube-hunter details"""
        self.details = json.loads(self.pod_log.splitlines()[-1])
        if self.details["vulnerabilities"]:
            self.result = 100
            msg = prettytable.PrettyTable(
                header_style='upper', padding_width=5,
                field_names=['category', 'vulnerability', 'severity'])
            severity = kwargs.get("severity", "none")
            if severity == "low":
                allowed_severity = []
            elif severity == "medium":
                allowed_severity = ["low"]
            elif severity == "high":
                allowed_severity = ["low", "medium"]
            else:
                self.__logger.warning(
                    "Just printing all vulnerabilities as "
                    "no severity criteria given")
                allowed_severity = ["low", "medium", "high"]
            for vulnerability in self.details["vulnerabilities"]:
                if vulnerability["severity"] not in allowed_severity:
                    self.result = 0
                msg.add_row(
                    [vulnerability["category"], vulnerability["vulnerability"],
                     vulnerability["severity"]])
            self.__logger.warning("\n\n%s\n", msg.get_string())
        if self.details["hunter_statistics"]:
            msg = prettytable.PrettyTable(
                header_style='upper', padding_width=5,
                field_names=['name', 'description', 'vulnerabilities'])
            for statistics in self.details["hunter_statistics"]:
                msg.add_row(
                    [statistics["name"],
                     textwrap.fill(statistics["description"], width=50),
                     statistics["vulnerabilities"]])
            self.__logger.info("\n\n%s\n", msg.get_string())

    def run(self, **kwargs):
        super().run(**kwargs)
        try:
            self.process_results(**kwargs)
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Cannot process results")
            self.result = 0


class KubeBench(SecurityTesting):
    """kube-bench checks whether Kubernetes is deployed securelyself.

    It runs the checks documented in the CIS Kubernetes Benchmark.

    See https://github.com/aquasecurity/kube-bench for more details
    """

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.job_name = "kube-bench"
        self.ns_generate_name = "kube-bench-"

    def run(self, **kwargs):
        self.job_name = f'kube-bench-{kwargs.get("target", "node")}'
        super().run(**kwargs)
        self.details["report"] = ast.literal_eval(self.pod_log)
        msg = prettytable.PrettyTable(
            header_style='upper', padding_width=5,
            field_names=['node_type', 'version', 'test_desc', 'pass',
                         'fail', 'warn'])
        for details in self.details["report"]["Controls"]:
            for test in details['tests']:
                msg.add_row(
                    [details['node_type'], details['version'], test['desc'],
                     test['pass'], test['fail'], test['warn']])
                for result in test["results"]:
                    if result['scored'] and result['status'] == 'FAIL':
                        self.__logger.error(
                            "%s\n%s", result['test_desc'],
                            result['remediation'])
        self.__logger.warning("Targets:\n\n%s\n", msg.get_string())
        self.result = 100
