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

import fnmatch
import logging
import os
import shutil
import subprocess
import time
import yaml

from xtesting.core import testcase


class CNFConformance(testcase.TestCase):
    """ Implement CNF Conformance driver.

    https://hackmd.io/@vulk/SkY54QnsU
    """

    src_dir = '/src/cnf-conformance'
    bin_dir = '/usr/local/bin'

    __logger = logging.getLogger(__name__)

    def setup(self, **kwargs):
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

    def run(self, **kwargs):
        """"Running the test with example CNF"""
        self.start_time = time.time()
        self.setup(**kwargs)
        # a previous results.yml leads to interactive mode
        if os.path.exists(os.path.join(self.res_dir, 'results.yml')):
            os.remove(os.path.join(self.res_dir, 'results.yml'))
        cmd = ['cnf-conformance', 'all']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        for lfile in os.listdir(self.res_dir):
            if fnmatch.fnmatch(lfile, 'cnf-conformance-results-*.yml'):
                with open(os.path.join(self.res_dir, lfile)) as yfile:
                    self.details = yaml.safe_load(yfile)
        self.result = 100
        self.stop_time = time.time()

    def clean(self):
        cmd = ['cnf-conformance', 'cnf_cleanup',
               'cnf-config=cnf-conformance.yml']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        shutil.rmtree(os.path.join(self.res_dir, 'tools'))
        shutil.rmtree(os.path.join(self.res_dir, 'cnfs'))
