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
[1] https://github.com/lfn-cnti/testsuite
"""

from __future__ import division

import logging
import os
import shutil
import subprocess
import time
import yaml

from kubernetes import client
from kubernetes import config
import prettytable
from xtesting.core import testcase


class CNFConformance(testcase.TestCase):
    # pylint: disable=too-many-instance-attributes
    """ Implement CNF Conformance driver.

    https://hackmd.io/@vulk/SkY54QnsU
    """

    src_dir = '/src/cnti-testsuite'
    bin_dir = '/usr/local/bin'
    results_file = 'cnti/results/latest.yml'
    default_tag = 'cert'
    default_cnf_config = 'example-cnfs/coredns/cnti-testsuite.yaml'

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config.load_kube_config()
        self.corev1 = client.CoreV1Api()
        self.output_log_name = 'functest-kubernetes.log'
        self.output_debug_log_name = 'functest-kubernetes.debug.log'
        self.cnf_config = ''

    def check_requirements(self):
        """Check if cnti-testsuite is in $PATH"""
        if not os.path.exists(os.path.join(self.bin_dir, 'cnti-testsuite')):
            self.__logger.warning(
                "cnti-testsuite is not compiled for arm and arm64 for the "
                "time being")
            self.is_skipped = True

    def setup(self):
        """Implement initialization and pre-reqs steps"""
        if os.path.exists(os.path.join(self.src_dir, "cnti")):
            shutil.rmtree(os.path.join(self.src_dir, "cnti"))
        os.chdir(self.src_dir)
        cmd = ['cnti-testsuite', 'setup']
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            self.__logger.exception(
                "Cannot run %s:\n%s", ' '.join(exc.cmd),
                exc.output.decode("utf-8"))
            self.result = 0
            return False
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        cmd = ['cnti-testsuite', 'cnf_install',
               '--cnf-config', self.cnf_config]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            self.__logger.exception(
                "Cannot run %s:\n%s", ' '.join(exc.cmd),
                exc.output.decode("utf-8"))
            self.result = 0
            return False
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        return True

    def load_results(self):
        """Read the results the test suite wrote for this run

        Returns False when the suite left no results file behind, which
        means it never got far enough to report anything.
        """
        results = os.path.join(self.src_dir, self.results_file)
        if not os.path.exists(results):
            self.__logger.error(
                "cnti-testsuite wrote no results file at %s", results)
            self.details = {}
            return False
        with open(results, encoding='utf-8') as yfile:
            self.details = yaml.safe_load(yfile)
        return True

    def get_score(self, tag, item_criteria):
        """Score the run from the summary block of the results file

        The test suite records every aggregate it prints on stdout in that
        block, so read the numbers from there rather than parsing the
        human-readable output. Fall back to counting the items when the
        block is missing.
        """
        status = self.details.get('status')
        if status == 'running':
            # The file reads 'running' until the suite reaches the end of
            # the run, so a run that died part-way leaves no verdict
            # behind: a partial tally must not be mistaken for one.
            self.__logger.error(
                "cnti-testsuite did not complete the run, its results "
                "still read '%s'", status)
            return 0
        summary = self.details.get('summary') or {}
        if tag == 'cert':
            return summary.get('essential_passed', item_criteria)
        max_points = summary.get('maximum_points')
        if max_points:
            return summary.get('points', 0) / max_points * 100
        items = self.details.get('items') or []
        return item_criteria / len(items) * 100 if items else 0

    def run_conformance(self, **kwargs):
        """Run CNF Conformance"""
        tag = kwargs.get("tag", self.default_tag)
        cmd = ['cnti-testsuite', tag]
        output = subprocess.run(
            cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
            check=False).stdout
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        if not self.load_results():
            self.result = 0
            return
        msg = prettytable.PrettyTable(
            header_style='upper', padding_width=5,
            field_names=['name', 'status'])
        item_criteria = 0
        for item in self.details['items']:
            msg.add_row([item['name'], item['status']])
            if item['status'] == "passed":
                item_criteria += 1
            elif item['status'] == "failed":
                self.__logger.warning("%s %s", item['name'], item['status'])
        self.__logger.info("\n\n%s\n", msg.get_string())
        self.result = self.get_score(tag, item_criteria)
        if not os.path.exists(self.res_dir):
            os.makedirs(self.res_dir)
        shutil.copy2(
            os.path.join(self.src_dir, self.results_file),
            os.path.join(self.res_dir, 'cnti-testsuite-results.yml'))

    def run(self, **kwargs):
        """"Running the test with example CNF"""
        self.start_time = time.time()
        self.cnf_config = kwargs.get("cnf-config", self.default_cnf_config)
        if self.setup():
            self.run_conformance(**kwargs)
        self.stop_time = time.time()

    def clean(self):
        for clean_cmd in ['cnf_uninstall', 'uninstall_all']:
            cmd = ['cnti-testsuite', clean_cmd,
                   '--cnf-config', self.cnf_config]
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        try:
            for namespace in ["cnti-testsuite", "cnti-default"]:
                self.corev1.delete_namespace(namespace)
                self.__logger.debug("delete_namespace: %s", namespace)
        except client.rest.ApiException:
            pass
        # cnti-testsuite cleanup does not wait for removing reources
        # use time.sleep(60) till
        # https://github.com/lfn-cnti/testsuite/issues/2194
        # is fixed
        time.sleep(60)
