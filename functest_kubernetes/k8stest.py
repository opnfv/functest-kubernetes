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
from pathlib import Path
import re
import subprocess
import time
import yaml

from xtesting.core import testcase


class E2ETesting(testcase.TestCase):
    """Kubernetes test runner"""
    # pylint: disable=too-many-instance-attributes

    __logger = logging.getLogger(__name__)

    config = f'{Path.home()}/.kube/config'
    gcr_repo = os.getenv("MIRROR_REPO", "gcr.io")
    k8s_gcr_repo = os.getenv("MIRROR_REPO", "k8s.gcr.io")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cmd = []
        self.dir_results = "/home/opnfv/functest/results"
        self.res_dir = os.path.join(self.dir_results, self.case_name)
        self.result = 0
        self.start_time = 0
        self.stop_time = 0
        self.output_log_name = 'functest-kubernetes.log'
        self.output_debug_log_name = 'functest-kubernetes.debug.log'

    @staticmethod
    def convert_ini_to_dict(value):
        "Convert oslo.conf input to dict"
        assert isinstance(value, str)
        try:
            return dict((x.rsplit(':', 1) for x in value.split(',')))
        except ValueError:
            return {}

    def run_kubetest(self, **kwargs):  # pylint: disable=too-many-branches
        """Run the test suites"""
        cmd_line = [
            'ginkgo', f'--nodes={kwargs.get("nodes", 1)}',
            '--no-color', '/usr/local/bin/e2e.test', '--',
            '-kubeconfig', self.config,
            '-provider', kwargs.get('provider', 'local'),
            '-report-dir', self.res_dir]
        for arg in kwargs.get("ginkgo", {}):
            cmd_line.extend([f'-ginkgo.{arg}', kwargs["ginkgo"][arg]])
        for key, value in self.convert_ini_to_dict(
                os.environ.get("E2E_TEST_OPTS", "")).items():
            cmd_line.extend([f'-{key}', value])
        if "NON_BLOCKING_TAINTS" in os.environ:
            cmd_line.extend(
                ['-non-blocking-taints', os.environ["NON_BLOCKING_TAINTS"]])
        cmd_line.extend(['-disable-log-dump'])
        self._generate_repo_list_file()
        self.__logger.info("Starting k8s test: '%s'.", cmd_line)
        env = os.environ.copy()
        env["KUBE_TEST_REPO_LIST"] = f"{self.res_dir}/repositories.yml"
        with subprocess.Popen(
                cmd_line, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, env=env) as process:
            boutput = process.stdout.read()
        with open(os.path.join(
                self.res_dir, 'e2e.log'), 'w', encoding='utf-8') as foutput:
            foutput.write(boutput.decode("utf-8"))
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
        if not os.path.exists(self.res_dir):
            os.makedirs(self.res_dir)
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
        gcr_repo = os.getenv("GCR_REPO", self.gcr_repo)
        k8s_gcr_repo = os.getenv("K8S_GCR_REPO", self.k8s_gcr_repo)
        repo_list = {
            "gcAuthenticatedRegistry":
                f"{gcr_repo}/authenticated-image-pulling",
            "e2eRegistry": f"{gcr_repo}/kubernetes-e2e-test-images",
            "promoterE2eRegistry": f"{k8s_gcr_repo}/e2e-test-images",
            "buildImageRegistry": f"{k8s_gcr_repo}/build-image",
            "invalidRegistry": "invalid.com/invalid",
            "gcEtcdRegistry": k8s_gcr_repo,
            "gcRegistry": k8s_gcr_repo,
            "sigStorageRegistry": f"{k8s_gcr_repo}/sig-storage",
            "privateRegistry": f"{gcr_repo}/k8s-authenticated-test",
            "sampleRegistry": f"{gcr_repo}/google-samples",
            "gcrReleaseRegistry": f"{gcr_repo}/gke-release",
            "microsoftRegistry": "mcr.microsoft.com"
        }
        with open(
                f"{self.res_dir}/repositories.yml", 'w',
                encoding='utf-8') as file:
            yaml.dump(repo_list, file)
