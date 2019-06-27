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

    @mock.patch('functest_kubernetes.k8stest.os.path.isfile')
    def test_error_logging(self, mock_isfile):
        # pylint: disable=unused-argument
        with mock.patch('functest_kubernetes.k8stest.'
                        'subprocess.Popen') as mock_popen, \
             mock.patch.object(self.k8stesting,
                               '_K8sTesting__logger') as mock_logger:
            mock_stdout = mock.Mock()
            attrs = {'stdout.read.return_value': 'Error loading client'}
            mock_stdout.configure_mock(**attrs)
            mock_popen.return_value = mock_stdout
            self.k8stesting.run()
            mock_logger.exception.assert_called_with(
                "Error with running kubetest:")

    @mock.patch('six.moves.builtins.open', mock.mock_open())
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
