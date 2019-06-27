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

import mock
from xtesting.core import testcase

from functest_kubernetes import k8stest


class K8sTests(unittest.TestCase):

    # pylint: disable=missing-docstring

    def setUp(self):
        os.environ["DEPLOY_SCENARIO"] = "k8-test"
        os.environ["KUBE_MASTER_IP"] = "127.0.0.1"
        os.environ["KUBE_MASTER_URL"] = "https://127.0.0.1:6443"
        os.environ["KUBERNETES_PROVIDER"] = "local"

        self.k8stesting = k8stest.K8sTesting()

    @mock.patch('functest_kubernetes.k8stest.os.path.isfile',
                return_value=False)
    def test_run_missing_config_file(self, mock_func):
        self.k8stesting.config = 'not_file'
        with mock.patch.object(self.k8stesting,
                               '_K8sTesting__logger') as mock_logger:
            self.assertEquals(self.k8stesting.run(),
                              testcase.TestCase.EX_RUN_ERROR)
            mock_logger.error.assert_called_with(
                "Cannot run k8s testcases. Config file not found")
        mock_func.assert_called_with('not_file')

    def test_run_kubetest_cmd_none(self):
        self.k8stesting.cmd = None
        with self.assertRaises(TypeError):
            self.k8stesting.run_kubetest()

    @mock.patch('re.search')
    @mock.patch('six.moves.builtins.open', mock.mock_open())
    @mock.patch('functest_kubernetes.k8stest.os.path.isfile')
    @mock.patch('functest_kubernetes.k8stest.subprocess.Popen')
    def test_run(self, *args):
        self.assertEquals(self.k8stesting.run(),
                          testcase.TestCase.EX_OK)
        for loop in range(3):
            args[loop].assert_called()


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    unittest.main(verbosity=2)
