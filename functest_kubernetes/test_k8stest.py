#!/usr/bin/env python
#
# Copyright (c) 2018 All rights reserved
# This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
#
# http://www.apache.org/licenses/LICENSE-2.0
#

"""Define the classes required to fully cover k8s."""

import logging
import os
import unittest

from functest_kubernetes import k8stest


class K8sTests(unittest.TestCase):

    # pylint: disable=missing-docstring

    def setUp(self):
        os.environ["DEPLOY_SCENARIO"] = "k8-test"
        os.environ["KUBE_MASTER_IP"] = "127.0.0.1"
        os.environ["KUBE_MASTER_URL"] = "https://127.0.0.1:6443"
        os.environ["KUBERNETES_PROVIDER"] = "local"

    def _test_no_env_var(self, var):
        del os.environ[var]
        with self.assertRaises(Exception):
            k8stest.K8sTesting().check_envs()

    def test_no_deploy_scenario(self):
        self._test_no_env_var("DEPLOY_SCENARIO")

    def test_no_kube_master_ip(self):
        self._test_no_env_var("KUBE_MASTER_IP")

    def test_no_kube_master_url(self):
        self._test_no_env_var("KUBE_MASTER_URL")

    def test_no_kubernetes_provider(self):
        self._test_no_env_var("KUBERNETES_PROVIDER")

    def test_run_kubetest_cmd_none(self):
        self.k8stesting.cmd = None
        with self.assertRaises(TypeError):
            self.k8stesting.run_kubetest()

    @mock.patch('functest_kubernetes.k8stest.os.path.isfile')
    @mock.patch('functest_kubernetes.k8stest.subprocess.Popen')
    def test_run(self, mock_open, mock_isfile):
        self.assertEquals(self.k8stesting.run(),
                          testcase.TestCase.EX_OK)
        mock_isfile.assert_called()
        mock_open.assert_called()


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    unittest.main(verbosity=2)
