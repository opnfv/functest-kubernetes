#!/usr/bin/env python

# Copyright (c) 2021 Orange and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

"""
Benchmarking Kubernetes Networking Performance
"""

import glob
import logging
import os
from pathlib import Path
import shutil
import subprocess
import time

from kubernetes import client
from kubernetes import config
from xtesting.core import testcase


class Netperf(testcase.TestCase):
    # pylint: disable=too-many-instance-attributes
    """Run Benchmarking Kubernetes Networking Performance"""

    ns_generate_name = "netperf-"
    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config.load_kube_config()
        self.corev1 = client.CoreV1Api()
        self.output_log_name = 'functest-kubernetes.log'
        self.output_debug_log_name = 'functest-kubernetes.debug.log'
        self.namespace = ''

    def check_requirements(self):
        """Check if launch is in $PATH"""
        self.is_skipped = not (
            shutil.which("launch") and shutil.which("plotperf"))
        if self.is_skipped:
            self.__logger.warning("launch or plotperf is missing")

    def run(self, **kwargs):
        self.start_time = time.time()
        try:
            if not os.path.exists(self.res_dir):
                os.makedirs(self.res_dir)
            os.chdir(self.res_dir)
            api_response = self.corev1.create_namespace(
                client.V1Namespace(metadata=client.V1ObjectMeta(
                    generate_name=self.ns_generate_name,
                    labels={
                        "pod-security.kubernetes.io/enforce": "baseline"})))
            self.namespace = api_response.metadata.name
            self.__logger.debug("create_namespace: %s", api_response)
            cmd = ['launch', '-iterations', '1', '-kubeConfig',
                   f'{Path.home()}/.kube/config',
                   '-namespace', self.namespace]
            output = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, timeout=3600)
            self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
            lfiles = glob.glob(os.path.join(
                f'results_{self.namespace}-latest',
                f'{self.namespace}-latest*.csv'))
            results = max(lfiles, key=os.path.getmtime)
            cmd = ['plotperf', '-c', results,
                   '-o', self.res_dir, '-s', 'netperf']
            output = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, timeout=60)
            self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
            self.result = 100
            status = testcase.TestCase.EX_OK
        except (subprocess.TimeoutExpired,
                subprocess.CalledProcessError) as exc:
            self.__logger.exception(
                "Cannot run %s:\n%s", ' '.join(exc.cmd),
                exc.output.decode("utf-8"))
            self.result = 0
            status = testcase.TestCase.EX_RUN_ERROR
        self.stop_time = time.time()
        return status

    def clean(self):
        if self.namespace:
            try:
                self.corev1.delete_namespace(self.namespace)
                self.__logger.debug("delete_namespace: %s", self.namespace)
            except client.rest.ApiException:
                pass
