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


class E2ETesting(testcase.TestCase):
    """Kubernetes test runner"""
    # pylint: disable=too-many-instance-attributes

    __logger = logging.getLogger(__name__)

    config = '/root/.kube/config'

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
        if kwargs.get("focus"):
            cmd_line.extend(['-ginkgo.focus', kwargs.get("focus")])
        if kwargs.get("skip"):
            cmd_line.extend(['-ginkgo.skip', kwargs.get("skip")])
        cmd_line.extend(['-disable-log-dump', 'true'])
        self.__logger.info("Starting k8s test: '%s'.", cmd_line)
        process = subprocess.Popen(cmd_line, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        boutput = process.stdout.read()
        with open(os.path.join(self.res_dir, 'e2e.log'), 'wb') as foutput:
            foutput.write(boutput)
        grp = re.search(
            r'^(FAIL|SUCCESS)!.* ([0-9]+) Passed \| ([0-9]+) Failed \|'
            r' ([0-9]+) Pending \| ([0-9]+) Skipped', boutput.decode("utf-8"),
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
                r'^(Summarizing [0-9]+ Failure.*)Ran', boutput.decode("utf-8"),
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
