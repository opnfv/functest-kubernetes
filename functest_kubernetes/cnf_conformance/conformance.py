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

import fnmatch
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
    default_tag = 'all'

    __logger = logging.getLogger(__name__)

    def setup(self):
        """Implement initialization and pre-reqs steps"""
        os.makedirs(self.res_dir, exist_ok=True)

        shutil.copy2(os.path.join(self.src_dir, 'points.yml'), self.res_dir)
        shutil.copy2(
            os.path.join(self.src_dir, 'cnf-conformance.yml'), self.res_dir)
        os.chdir(self.res_dir)
        # cnf-conformance must be in the working dir
        # https://github.com/cncf/cnf-conformance/issues/388
        if not os.path.exists(os.path.join(self.res_dir, 'cnf-conformance')):
            os.symlink(
                os.path.join(self.bin_dir, 'cnf-conformance'),
                os.path.join(self.res_dir, 'cnf-conformance'))
        cmd = ['cnf-conformance', 'setup']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        cmd = ['cnf-conformance', 'cnf_setup',
               'cnf-config=cnf-conformance.yml']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))

    def run_conformance(self, **kwargs):
        """Run CNF Conformance"""
        # a previous results.yml leads to interactive mode
        if os.path.exists(os.path.join(self.res_dir, 'results.yml')):
            os.remove(os.path.join(self.res_dir, 'results.yml'))
        cmd = ['cnf-conformance', kwargs.get("tag", self.default_tag)]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        for lfile in os.listdir(self.res_dir):
            if fnmatch.fnmatch(lfile, 'cnf-conformance-results-*.yml'):
                with open(os.path.join(self.res_dir, lfile)) as yfile:
                    self.details = yaml.safe_load(yfile)
                    msg = prettytable.PrettyTable(
                        header_style='upper', padding_width=5,
                        field_names=['name', 'status'])
                    for item in self.details['items']:
                        msg.add_row([item['name'], item['status']])
                    self.__logger.info("\n\n%s\n", msg.get_string())
        grp = re.search(r'Final score: (\d+) of (\d+)', output.decode("utf-8"))
        if grp:
            self.result = int(grp.group(1)) / int(grp.group(2)) * 100

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
        shutil.rmtree(self.res_dir)
