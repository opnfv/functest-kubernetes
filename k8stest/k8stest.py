#!/usr/bin/env python
#
# Copyright (c) 2015 All rights reserved
# This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
#
# http://www.apache.org/licenses/LICENSE-2.0
#

from __future__ import division

import logging
import subprocess
import time

from functest.core import testcase


""" logging configuration """
logger = logging.getLogger('functest.ci')


class K8sTesting(testcase.TestCase):

    def __init__(self, **kwargs):
        super(K8sTesting, self).__init__(**kwargs)
        self.CMD = ''

    def run_kubetest(self):
        cmd_line = self.CMD
        logger.info("Starting k8s test: '%s'." % cmd_line)

        p = subprocess.Popen(
            cmd_line, shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        remark = []
        lines = p.stdout.readlines()
        for i in range(len(lines)-1, -1, -1):
            new_line = str(lines[i])

            if 'SUCCESS!' in new_line or 'FAIL!' in new_line:
                remark = new_line.replace('--', '|').split('|')
                break

        for val in remark:
            logger.info(val)
            if 'Passed' in val:
                num_success = val[1]
            elif 'Skipped' in val:
                num_skipped = val[1]
            elif 'Failed' in val:
                num_failures = val[1]

        if remark and 'SUCCESS!' in remark[0]:
            self.result = 100
        else:
            self.result = 0


    def run(self):

        self.start_time = time.time()
        try:
            self.run_kubetest()
            res = testcase.TestCase.EX_OK
        except Exception as e:
            logger.error('Error with run: %s' % e)
            res = testcase.TestCase.EX_RUN_ERROR

        self.stop_time = time.time()
        return res


class K8sSmokeTest(K8sTesting):

    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs["case_name"] = 'k8s_e2e_testing'
        K8sTesting.__init__(self, **kwargs)
        self.CMD = '/src/k8s.io/kubernetes/cluster/test-smoke.sh --host=$KUBE_MASTER_URL'
