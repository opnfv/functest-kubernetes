#!/usr/bin/env python

import logging
import os
import time

from rally import api
from rally.env import env_mgr
from rally.cli import envutils
from rally.common import fileutils
from rally.common import yamlutils as yaml

from xtesting.core import testcase


class Kubernetes(testcase.TestCase):

    __logger = logging.getLogger(__name__)

    def run(self, **kwargs):
        self.start_time = time.time()
        rapi = api.API()
        spec = env_mgr.EnvManager.create_spec_from_sys_environ()["spec"]
        env = env_mgr.EnvManager.create('my-kubernetes', spec)
        data = env.check_health()
        self.__logger.info("check health: %s", data)
        if not data['existing@kubernetes']['available']:
            self.__logger.error(
                "Cannot check env heath: %s",
                data['existing@kubernetes']['message'])
            self.result = 0
            return
        fileutils.update_globals_file(envutils.ENV_ENV, env.uuid)
        input_task = open(
            '/src/rally-openstack/xrally_tasks/all-in-one.yaml').read()
        task_dir = os.path.expanduser(
            os.path.dirname(
                '/src/rally-openstack/xrally_tasks/all-in-one.yaml'))
        task_args = {}
        rendered_task = rapi.task.render_template(
            task_template=input_task, template_dir=task_dir, **task_args)
        parsed_task = yaml.safe_load(rendered_task)
        rapi.task.validate(deployment='my-kubernetes', config=parsed_task)
        task_instance = rapi.task.create(deployment='my-kubernetes')
        self.__logger.info("task %s", task_instance)
        result = rapi.task.start(
            deployment='my-kubernetes',
            config=parsed_task,
            task=task_instance["uuid"])
        self.__logger.info("result %s", result)
        result = rapi.task.get(task_instance["uuid"], detailed=True)
        self.__logger.info("result %s", result)
        if result['pass_sla']:
            self.result = 100
        result = rapi.task.export(
            task_instance["uuid"], "html",
            output_dest="/root/output.html")
        self.__logger.info("result %s", result)
        self.stop_time = time.time()
