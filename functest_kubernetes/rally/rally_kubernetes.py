#!/usr/bin/env python

"""Run workloads via Rally against Kubernetes platform

xrally/kubernetes_ provides xRally plugins for Kubernetes platform.

.. _xrally/kubernetes: https://github.com/xrally/xrally-kubernetes/
"""

import logging
import os
import time

import pkg_resources
from rally import api
from rally import exceptions
from rally.common import yamlutils as yaml
import rally.common.logging
from rally.env import env_mgr

from xtesting.core import testcase


class RallyKubernetes(testcase.TestCase):
    """Run tasks for checking basic functionality of Kubernetes cluster"""

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(RallyKubernetes, self).__init__(**kwargs)
        self.dir_results = "/home/opnfv/functest/results"
        self.res_dir = os.path.join(self.dir_results, self.case_name)

    def run(self, **kwargs):
        self.start_time = time.time()
        if not os.path.exists(self.res_dir):
            os.makedirs(self.res_dir)
        rapi = api.API()
        api.CONF.set_default("use_stderr", False)
        api.CONF.set_default('log_dir', self.res_dir)
        api.CONF.set_default('log_file', 'rally.log')
        rally.common.logging.setup("rally")
        spec = env_mgr.EnvManager.create_spec_from_sys_environ()["spec"]
        try:
            env_mgr.EnvManager.get('my-kubernetes').delete(force=True)
        except exceptions.DBRecordNotFound:
            pass
        env = env_mgr.EnvManager.create('my-kubernetes', spec)
        result = env.check_health()
        self.__logger.debug("check health %s: %s", 'my-kubernetes', result)
        if not result['existing@kubernetes']['available']:
            self.__logger.error(
                "Cannot check env heath: %s",
                result['existing@kubernetes']['message'])
            return
        input_task = open(
            pkg_resources.resource_filename(
                'functest_kubernetes', 'rally/all-in-one.yaml')).read()
        task = yaml.safe_load(input_task)
        rapi.task.validate(deployment='my-kubernetes', config=task)
        task_instance = rapi.task.create(deployment='my-kubernetes')
        rapi.task.start(
            deployment='my-kubernetes', config=task,
            task=task_instance["uuid"])
        self.details = rapi.task.get(task_instance["uuid"], detailed=True)
        self.__logger.debug("details: %s", self.details)
        if self.details['pass_sla']:
            self.result = 100
        result = rapi.task.export(
            [task_instance["uuid"]], "html",
            output_dest=os.path.join(
                self.res_dir, "{}.html".format(self.case_name)))
        if "files" in result:
            for path in result["files"]:
                with open(path, "w+") as output:
                    output.write(result["files"][path])
        result = rapi.task.export(
            [task_instance["uuid"]], "junit-xml",
            output_dest=os.path.join(
                self.res_dir, "{}.xml".format(self.case_name)))
        if "files" in result:
            for path in result["files"]:
                with open(path, "w+") as output:
                    output.write(result["files"][path])
        self.stop_time = time.time()
