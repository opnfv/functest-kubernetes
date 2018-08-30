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

from xtesting.core import testcase


class K8sTesting(testcase.TestCase):
    """Kubernetes test runner"""

    __logger = logging.getLogger(__name__)

    config = '/root/.kube/config'

    def __init__(self, **kwargs):
        super(K8sTesting, self).__init__(**kwargs)
        self.cmd = []
        self.result = 0
        self.start_time = 0
        self.stop_time = 0

    def run_kubetest(self):  # pylint: disable=too-many-branches
        """Run the test suites"""
        cmd_line = self.cmd
        self.__logger.info("Starting k8s test: '%s'.", cmd_line)

        process = subprocess.Popen(cmd_line, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        output = process.stdout.read()
        # Remove color code escape sequences
        output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', str(output))

        if ('Error loading client' in output or
                'Unexpected error' in output):
            raise Exception(output)

        remarks = []
        lines = output.split('\n')
        success = False
        failure = False
        i = 0
        while i < len(lines):
            if '[Fail]' in lines[i] or 'Failures:' in lines[i]:
                self.__logger.error(lines[i])
            if re.search(r'\[(.)*[0-9]+ seconds\]', lines[i]):
                self.__logger.debug(lines[i])
                i = i + 1
                while i < len(lines) and lines[i] != '-' * len(lines[i]):
                    if lines[i].startswith('STEP:') or ('INFO:' in lines[i]):
                        break
                    self.__logger.debug(lines[i])
                    i = i + 1
            if i >= len(lines):
                break
            success = 'SUCCESS!' in lines[i]
            failure = 'FAIL!' in lines[i]
            if success or failure:
                if i != 0 and 'seconds' in lines[i - 1]:
                    remarks.append(lines[i - 1])
                remarks = remarks + lines[i].replace('--', '|').split('|')
                break
            i = i + 1

        self.__logger.debug('-' * 10)
        self.__logger.info("Remarks:")
        for remark in remarks:
            if 'seconds' in remark:
                self.__logger.debug(remark)
            elif 'Passed' in remark:
                self.__logger.info("Passed: %s", remark.split()[0])
            elif 'Skipped' in remark:
                self.__logger.info("Skipped: %s", remark.split()[0])
            elif 'Failed' in remark:
                self.__logger.info("Failed: %s", remark.split()[0])

        if success:
            self.result = 100
        elif failure:
            self.result = 0

    def run(self, **kwargs):

        if not os.path.isfile(self.config):
            self.__logger.error(
                "Cannot run k8s testcases. Config file not found")
            return self.EX_RUN_ERROR

        self.start_time = time.time()
        try:
            self.run_kubetest()
            res = self.EX_OK
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Error with running kubetest:")
            res = self.EX_RUN_ERROR

        self.stop_time = time.time()
        return res


class K8sSmokeTest(K8sTesting):
    """Kubernetes smoke test suite"""
    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs.get("case_name", 'k8s_smoke')
        super(K8sSmokeTest, self).__init__(**kwargs)
        self.cmd = ["/src/k8s.io/kubernetes/_output/bin/e2e.test",
                    "-ginkgo.focus", "Guestbook.application",
                    "-kubeconfig", self.config, "--provider", "local"]


class K8sConformanceTest(K8sTesting):
    """Kubernetes conformance test suite"""
    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs.get("case_name", 'k8s_conformance')
        super(K8sConformanceTest, self).__init__(**kwargs)
        self.cmd = ['/src/k8s.io/kubernetes/_output/bin/e2e.test',
                    '-ginkgo.focus', 'Conformance',
                    '-kubeconfig', self.config, "--provider", "local"]
