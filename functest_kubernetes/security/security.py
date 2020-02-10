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
import subprocess
import time

from xtesting.core import testcase
from kubernetes import client, config


class SecurityTesting(testcase.TestCase):
    """Security test runner"""

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(SecurityTesting, self).__init__(**kwargs)
        self.cmd = []
        self.result = 0
        self.details = {}
        self.start_time = 0
        self.stop_time = 0
        self.error_string = ""

    def run_security(self):  # pylint: disable=too-many-branches
        """Run the test suites"""
        cmd_line = self.cmd
        self.__logger.info("Starting k8s test: '%s'.", cmd_line)

        process = subprocess.Popen(cmd_line, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        output = process.stdout.read().decode("utf-8")
        if ('Error loading client' in output or
                'Unexpected error' in output):
            raise Exception(output)

        # create a log file
        file_name = "/var/lib/xtesting/results/" + self.case_name + ".log"
        log_file = open(file_name, "w")
        log_file.write(output)
        log_file.close()

        # we consider the command return code for success criteria
        if process.returncode is None:
            success = False
            details = self.error_string
            if (self.case_name == 'kube_hunter' and
                    "No vulnerabilities were found" in output):
                success = True
        elif process.returncode != 0:
            success = False
            details = self.error_string
        else:
            success = True
            details = "Test PASS"

        self.details = details
        self.__logger.info("details: %s", details)

        if success:
            self.result = 100
        else:
            self.result = 0

    def run(self, **kwargs):
        """Generic Run."""

        self.start_time = time.time()
        try:
            self.run_security()
            res = self.EX_OK
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Error with running Security tests:")
            res = self.EX_RUN_ERROR

        self.stop_time = time.time()
        return res


class KubeHunter(SecurityTesting):
    """Check k8s vulnerabilities."""
    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs.get("case_name", 'kube_hunter')
        super(KubeHunter, self).__init__(**kwargs)
        config.load_kube_config(config_file='/root/.kube/config')
        kube_client = client.CoreV1Api()
        node_list = kube_client.list_node()
        kube_hunter_cmd = ['kube-hunter', '--remote']
        for i in node_list.items:
            addresses = i.status.addresses
            for j in addresses:
                if "External" in str(j):
                    kube_hunter_cmd.append(j.address)
        self.cmd = kube_hunter_cmd
        self.error_string = "Vulnerabilties detected."
