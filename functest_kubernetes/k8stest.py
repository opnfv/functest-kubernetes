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


LOGGER = logging.getLogger(__name__)


class K8sTesting(testcase.TestCase):
    """Kubernetes test runner"""

    def __init__(self, **kwargs):
        super(K8sTesting, self).__init__(**kwargs)
        self.cmd = []
        self.result = 0
        self.start_time = 0
        self.stop_time = 0

    def run_kubetest(self):  # pylint: disable=too-many-branches
        """Run the test suites"""
        cmd_line = self.cmd
        LOGGER.info("Starting k8s test: '%s'.", cmd_line)

        process = subprocess.Popen(cmd_line, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        output = process.stdout.read()
        # Remove color code escape sequences
        output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', str(output))

        file_logger = logging.getLogger(self.case_name)
        remarks = []
        lines = output.split('\n')
        i = 0
        while i < len(lines):
            if '[k8s.io]' in lines[i]:
                if i != 0 and 'seconds' in lines[i-1]:
                    file_logger.debug(lines[i-1])
                while lines[i] != '-'*len(lines[i]):
                    if lines[i].startswith('STEP:') or ('INFO:' in lines[i]):
                        break
                    file_logger.debug(lines[i])
                    i = i+1

            success = 'SUCCESS!' in lines[i]
            failure = 'FAIL!' in lines[i]
            if success or failure:
                if i != 0 and 'seconds' in lines[i-1]:
                    remarks.append(lines[i-1])
                remarks = remarks + lines[i].replace('--', '|').split('|')
                break
            i = i+1

        file_logger.debug('-'*10)
        file_logger.debug("Remarks:")
        for remark in remarks:
            if 'seconds' in remark:
                file_logger.debug(remark)
            elif 'Passed' in remark:
                file_logger.debug("Passed: %s", remark.split()[0])
            elif 'Skipped' in remark:
                file_logger.debug("Skipped: %s", remark.split()[0])
            elif 'Failed' in remark:
                file_logger.debug("Failed: %s", remark.split()[0])

        if success:
            self.result = 100
        elif failure:
            self.result = 0

    def run(self, **kwargs):

        if not os.path.isfile(os.getenv('KUBECONFIG')):
            LOGGER.error("Cannot run k8s testcases. Config file not found ")
            return self.EX_RUN_ERROR

        self.start_time = time.time()
        try:
            self.run_kubetest()
            res = self.EX_OK
        except Exception as ex:  # pylint: disable=broad-except
            LOGGER.error("Error with running %s", str(ex))
            res = self.EX_RUN_ERROR

        self.stop_time = time.time()
        return res

    def check_envs(self):  # pylint: disable=no-self-use
        """Check if required environment variables are set"""
        try:
            assert 'DEPLOY_SCENARIO' in os.environ
            assert 'KUBECONFIG' in os.environ
            assert 'KUBE_MASTER_IP' in os.environ
            assert 'KUBERNETES_PROVIDER' in os.environ
            assert 'KUBE_MASTER_URL' in os.environ
        except Exception as ex:
            raise Exception("Cannot run k8s testcases. "
                            "Please check env var: %s" % str(ex))


class K8sSmokeTest(K8sTesting):
    """Kubernetes smoke test suite"""
    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs.get("case_name", 'k8s_smoke')
        super(K8sSmokeTest, self).__init__(**kwargs)
        self.check_envs()
        self.cmd = ['/src/k8s.io/kubernetes/cluster/test-smoke.sh', '--host',
                    os.getenv('KUBE_MASTER_URL')]


class K8sConformanceTest(K8sTesting):
    """Kubernetes conformance test suite"""
    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs.get("case_name", 'k8s_conformance')
        super(K8sConformanceTest, self).__init__(**kwargs)
        self.check_envs()
        self.cmd = ['/src/k8s.io/kubernetes/_output/bin/e2e.test',
                    '--ginkgo.focus', 'Conformance']
