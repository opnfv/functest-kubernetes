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

from xtesting.core import testcase


class Netperf(testcase.TestCase):
    """Run Benchmarking Kubernetes Networking Performance"""

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_log_name = 'functest-kubernetes.log'
        self.output_debug_log_name = 'functest-kubernetes.debug.log'

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
            cmd = ['launch', '-iterations', '1', '-kubeConfig',
                   f'{Path.home()}/.kube/config']
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
            lfiles = glob.glob(os.path.join(
                'results_netperf-latest', 'netperf-latest*.csv'))
            results = max(lfiles, key=os.path.getmtime)
            shutil.move(results, os.path.join(self.res_dir, 'netperf.csv'))
            cmd = ['plotperf', '-c',
                   os.path.join(self.res_dir, 'netperf.csv'),
                   '-o', self.res_dir, '-s', 'netperf']
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
            self.result = 100
            status = testcase.TestCase.EX_OK
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Can not run Netperf")
            self.result = 0
            status = testcase.TestCase.EX_RUN_ERROR
        self.stop_time = time.time()
        return status
