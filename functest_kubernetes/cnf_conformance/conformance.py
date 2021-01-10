#!/usr/bin/env python

# Copyright (c) 2020 Orange and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

"""
The CNF Conformance program enables interoperability of Cloud native Network
Functions (CNFs) from multiple vendors running on top of Kubernetes supplied by
different vendors [1].
[1] https://github.com/cncf/cnf-conformance
"""

from __future__ import division

import glob
import logging
import os
import re
import shutil
import subprocess
import time
import yaml

import prettytable

from xtesting.core import testcase


class CNFConformance(testcase.TestCase):
    """ Implement CNF Conformance driver.

    https://hackmd.io/@vulk/SkY54QnsU
    """

    src_dir = '/src/cnf-conformance'
    bin_dir = '/usr/local/bin'
    default_tag = 'workload'

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(CNFConformance, self).__init__(**kwargs)
        self.output_log_name = 'functest-kubernetes.log'
        self.output_debug_log_name = 'functest-kubernetes.debug.log'

    def check_requirements(self):
        """Check if cnf-conformance is in $PATH"""
        if not os.path.exists(os.path.join(self.bin_dir, 'cnf-conformance')):
            self.__logger.warning(
                "cnf-conformance is not compiled for arm and arm64 for the "
                "time being")
            self.is_skipped = True

    def setup(self):
        """Implement initialization and pre-reqs steps"""
        if os.path.exists(self.res_dir):
            shutil.rmtree(self.res_dir)
        os.makedirs(self.res_dir)
        shutil.copy2(os.path.join(self.src_dir, 'points.yml'), self.res_dir)
        shutil.copy2(
            os.path.join(self.src_dir, 'cnf-conformance.yml'), self.res_dir)
        os.makedirs(os.path.join(self.res_dir, 'spec/fixtures'))
        for cfile in ["chaos_network_loss.yml", "chaos_cpu_hog.yml",
                      "chaos_container_kill.yml"]:
            shutil.copy2(
                os.path.join(self.src_dir, 'spec/fixtures', cfile),
                os.path.join(self.res_dir, 'spec/fixtures', cfile))
        os.chdir(self.res_dir)
        cmd = ['cnf-conformance', 'setup']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        cmd = ['cnf-conformance', 'cnf_setup',
               'cnf-config=cnf-conformance.yml']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))

    def run_conformance(self, **kwargs):
        """Run CNF Conformance"""
        cmd = ['cnf-conformance', kwargs.get("tag", self.default_tag)]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        lfiles = glob.glob(os.path.join(
            self.res_dir, 'results', 'cnf-conformance-results-*.yml'))
        results = max(lfiles, key=os.path.getmtime)
        with open(os.path.join(self.res_dir, 'results', results)) as yfile:
            self.details = yaml.safe_load(yfile)
            msg = prettytable.PrettyTable(
                header_style='upper', padding_width=5,
                field_names=['name', 'status'])
            for item in self.details['items']:
                msg.add_row([item['name'], item['status']])
            self.__logger.info("\n\n%s\n", msg.get_string())
        grp = re.search(
            r'Final .* score: (\d+) of (\d+)', output.decode("utf-8"))
        if grp:
            self.result = int(grp.group(1)) / int(grp.group(2)) * 100
        shutil.copy2(
            os.path.join(self.res_dir, 'results', results), self.res_dir)

    def run(self, **kwargs):
        """"Running the test with example CNF"""
        self.start_time = time.time()
        try:
            self.setup()
            self.run_conformance(**kwargs)
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Can not run CNF Conformance")
        self.stop_time = time.time()

    def clean(self):
        cmd = ['cnf-conformance', 'cnf_cleanup',
               'cnf-config=cnf-conformance.yml']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        shutil.rmtree(os.path.join(self.res_dir, 'tools'), ignore_errors=True)
        shutil.rmtree(os.path.join(self.res_dir, 'cnfs'), ignore_errors=True)
        shutil.rmtree(
            os.path.join(self.res_dir, 'results'), ignore_errors=True)
