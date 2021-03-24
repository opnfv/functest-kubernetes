#!/usr/bin/env python
#
# Copyright (c) 2018 All rights reserved
# This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
#
# http://www.apache.org/licenses/LICENSE-2.0
#

"""
Define the parent for Kubernetes testing.
"""

from __future__ import division

import logging
import os
import re
import subprocess
import time

from jinja2 import Template
from xtesting.core import testcase


class E2ETesting(testcase.TestCase):
    """Kubernetes test runner"""
    # pylint: disable=too-many-instance-attributes

    __logger = logging.getLogger(__name__)

    config = '/root/.kube/config'
    dockerhub_repo = os.getenv("MIRROR_REPO", "docker.io")
    gcr_repo = os.getenv("MIRROR_REPO", "gcr.io")
    k8s_gcr_repo = os.getenv("MIRROR_REPO", "k8s.gcr.io")

    def __init__(self, **kwargs):
        super(E2ETesting, self).__init__(**kwargs)
        self.cmd = []
        self.dir_results = "/home/opnfv/functest/results"
        self.res_dir = os.path.join(self.dir_results, self.case_name)
        self.result = 0
        self.start_time = 0
        self.stop_time = 0
        self.output_log_name = 'functest-kubernetes.log'
        self.output_debug_log_name = 'functest-kubernetes.debug.log'

    def run_kubetest(self, **kwargs):  # pylint: disable=too-many-branches
        """Run the test suites"""
        cmd_line = ['e2e.test', '-ginkgo.noColor', '-kubeconfig', self.config,
                    '-provider', 'local', '-report-dir', self.res_dir]
        for arg in kwargs:
            cmd_line.extend(['-ginkgo.{}'.format(arg), kwargs.get(arg)])
        if "NON_BLOCKING_TAINTS" in os.environ:
            cmd_line.extend(
                ['-non-blocking-taints', os.environ["NON_BLOCKING_TAINTS"]])
        cmd_line.extend(['-disable-log-dump', 'true'])
        self._generate_repo_list_file()
        self.__logger.info("Starting k8s test: '%s'.", cmd_line)
        env = os.environ.copy()
        env["GINKGO_PARALLEL"] = 'y'
        env["KUBE_TEST_REPO_LIST"] = "{}/repositories.yml".format(self.res_dir)"
        process = subprocess.Popen(cmd_line, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, env=env)
        boutput = process.stdout.read()
        with open(os.path.join(self.res_dir, 'e2e.log'), 'wb') as foutput:
            foutput.write(boutput)
        grp = re.search(
            r'^(FAIL|SUCCESS)!.* ([0-9]+) Passed \| ([0-9]+) Failed \|'
            r' ([0-9]+) Pending \| ([0-9]+) Skipped',
            boutput.decode("utf-8", errors="ignore"),
            re.MULTILINE | re.DOTALL)
        assert grp
        self.details['passed'] = int(grp.group(2))
        self.details['failed'] = int(grp.group(3))
        self.details['pending'] = int(grp.group(4))
        self.details['skipped'] = int(grp.group(5))
        self.__logger.debug("details: %s", self.details)
        self.result = self.details['passed'] * 100 / (
            self.details['passed'] + self.details['failed'] +
            self.details['pending'])
        self.__logger.debug("result: %s", self.result)
        if grp.group(1) == 'FAIL':
            grp2 = re.search(
                r'^(Summarizing [0-9]+ Failure.*)Ran',
                boutput.decode("utf-8", errors="ignore"),
                re.MULTILINE | re.DOTALL)
            if grp2:
                self.__logger.error(grp2.group(1))

    def run(self, **kwargs):
        if not os.path.isfile(self.config):
            self.__logger.error(
                "Cannot run k8s testcases. Config file not found")
            return self.EX_RUN_ERROR
        self.start_time = time.time()
        try:
            self.run_kubetest(**kwargs)
            res = self.EX_OK
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Error with running kubetest:")
            res = self.EX_RUN_ERROR
        self.stop_time = time.time()
        return res

    def _generate_repo_list_file(self):
        """Generate the repositories list for the test."""
        # The list is taken from
        # https://github.com/kubernetes/kubernetes/blob/master/test/utils/image/manifest.go
        # It may needs update regularly
        dockerhub_repo = os.getenv("DOCKERHUB_REPO", self.dockerhub_repo)
        gcr_repo = os.getenv("GCR_REPO", self.gcr_repo)
        k8s_gcr_repo = os.getenv("K8S_GCR_REPO", self.k8s_gcr_repo)
        repo_list = {
            "GcAuthenticatedRegistry": "{}/authenticated-image-pulling".format(
                gcr_repo),
            "E2eRegistry":             "{}/kubernetes-e2e-test-images".format(
                gcr_repo),
            "PromoterE2eRegistry":     "{}/e2e-test-images".format(
                k8s_gcr_repo),
            "BuildImageRegistry":      "{}/build-image".format(k8s_gcr_repo),
            "InvalidRegistry":         "invalid.com/invalid",
            "GcEtcdRegistry":          "{}".format(k8s_gcr_repo),
            "GcRegistry":              "{}".format(k8s_gcr_repo),
            "SigStorageRegistry":      "{}/sig-storage".format(k8s_gcr_repo),
            "PrivateRegistry":         "{}/k8s-authenticated-test".format(
                gcr_repo),
            "SampleRegistry":          "{}/google-samples".format(gcr_repo),
            "GcrReleaseRegistry":      "{}/gke-release".format(gcr_repo),
            "MicrosoftRegistry":       "mcr.microsoft.com",
        }
        with open("{}/repositories.yml".format(self.res_dir), 'w') as file:
            yaml.dump(repo_list, file)
