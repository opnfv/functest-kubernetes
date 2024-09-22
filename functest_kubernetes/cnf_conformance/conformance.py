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
[1] https://github.com/cncf/cnf-testsuite
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

from kubernetes import client
from kubernetes import config
import prettytable
from xtesting.core import testcase


class CNFConformance(testcase.TestCase):
    # pylint: disable=too-many-instance-attributes
    """ Implement CNF Conformance driver.

    https://hackmd.io/@vulk/SkY54QnsU
    """

    src_dir = '/src/cnf-testsuite'
    bin_dir = '/usr/local/bin'
    default_tag = 'cert'

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config.load_kube_config()
        self.corev1 = client.CoreV1Api()
        self.output_log_name = 'functest-kubernetes.log'
        self.output_debug_log_name = 'functest-kubernetes.debug.log'

    def check_requirements(self):
        """Check if cnf-testsuite is in $PATH"""
        if not os.path.exists(os.path.join(self.bin_dir, 'cnf-testsuite')):
            self.__logger.warning(
                "cnf-testsuite is not compiled for arm and arm64 for the "
                "time being")
            self.is_skipped = True

    def setup(self):
        """Implement initialization and pre-reqs steps"""
        if os.path.exists(os.path.join(self.src_dir, "results")):
            shutil.rmtree(os.path.join(self.src_dir, "results"))
        api_response = self.corev1.list_namespace()
        for namespace in ["cnf-testsuite", "default", "litmus"]:
            for item in api_response.items:
                if item.metadata.name == namespace:
                    self.corev1.patch_namespace(
                        namespace,
                        client.V1Namespace(metadata=client.V1ObjectMeta(
                            labels={
                                "pod-security.kubernetes.io/enforce":
                                    "privileged"})))
                    self.__logger.debug(
                        "patch_namespace: %s", namespace)
                    break
            else:
                self.corev1.create_namespace(
                    client.V1Namespace(metadata=client.V1ObjectMeta(
                        name=namespace, labels={
                            "pod-security.kubernetes.io/enforce":
                                "privileged"})))
                self.__logger.debug(
                    "create_namespace: %s", namespace)
        os.chdir(self.src_dir)
        cmd = ['cnf-testsuite', 'setup', '-l', 'debug']
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            self.__logger.exception(
                "Cannot run %s:\n%s", ' '.join(exc.cmd),
                exc.output.decode("utf-8"))
            self.result = 0
            return False
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        cmd = ['cnf-testsuite', 'cnf_setup',
               'cnf-config=cnf-testsuite.yml', '-l', 'debug']
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

    def run_conformance(self, **kwargs):
        """Run CNF Conformance"""
        cmd = ['cnf-testsuite', kwargs.get("tag", self.default_tag),
               '-l', 'debug']
        output = subprocess.run(
            cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
            check=False).stdout
        self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        lfiles = glob.glob(os.path.join(
            self.src_dir, 'results', 'cnf-testsuite-results-*.yml'))
        results = max(lfiles, key=os.path.getmtime)
        with open(os.path.join(
                self.src_dir, 'results', results), encoding='utf-8') as yfile:
            self.details = yaml.safe_load(yfile)
            msg = prettytable.PrettyTable(
                header_style='upper', padding_width=5,
                field_names=['name', 'status'])
            item_criteria = 0
            for item in self.details['items']:
                msg.add_row([item['name'], item['status']])
                if item['status'] == "passed":
                    item_criteria += 1
                elif item['status'] == "failed":
                    self.__logger.warning(
                        "%s %s", item['name'], item['status'])
            self.__logger.info("\n\n%s\n", msg.get_string())
        grp = re.search(
            r'(\d+) of (\d+) essential tests passed', output.decode("utf-8"))
        if grp:
            # https://github.com/cncf/cnf-certification/blob/main/reviewing.md
            self.result = int(grp.group(1))
        else:
            self.result = 0
        if not os.path.exists(self.res_dir):
            os.makedirs(self.res_dir)
        shutil.copy2(
            os.path.join(self.src_dir, 'results', results),
            os.path.join(self.res_dir, 'cnf-testsuite-results.yml'))

    def run(self, **kwargs):
        """"Running the test with example CNF"""
        self.start_time = time.time()
        if self.setup():
            self.run_conformance(**kwargs)
        self.stop_time = time.time()

    def clean(self):
        for clean_cmd in ['cnf_cleanup']:
            cmd = ['cnf-testsuite', clean_cmd,
                   'cnf-config=cnf-testsuite.yml']
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            self.__logger.info("%s\n%s", " ".join(cmd), output.decode("utf-8"))
        try:
            for namespace in ["cnf-testsuite", "litmus"]:
                self.corev1.delete_namespace(namespace)
                self.__logger.debug("delete_namespace: %s", namespace)
        except client.rest.ApiException:
            pass
