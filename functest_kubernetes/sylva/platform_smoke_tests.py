#!/usr/bin/env python

# pylint: disable=missing-docstring

import logging
import os
import time

from kubernetes import client
from kubernetes import config
from xtesting.core import testcase


class CniInstallation(testcase.TestCase):

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config.load_kube_config()
        self.appsv1 = client.AppsV1Api()
        self.apiv1ext = client.ApiextensionsV1Api()

    def check_requirements(self):
        if (not os.getenv("CNI_DAEMON_SETS") and not os.getenv("CNI_CRDS")):
            self.is_skipped = True
            self.__logger.warning(
                "Please set CNI_DAEMON_SETS or CNI_CRDS in env")

    def search_cni(self, cluster_daemon_sets, cni_ds):
        self.__logger.info(
            "cluster_daemon_sets: %s, cni_ds: %s",
            cluster_daemon_sets, cni_ds)
        for i in cluster_daemon_sets.items:
            if cni_ds in i.metadata.name:
                ds_name = i.metadata.name
                ds_ns = i.metadata.namespace
                ds_data = self.appsv1.read_namespaced_daemon_set(
                    namespace=ds_ns, name=ds_name)
                self.__logger.info("ds_data: %s", ds_data)
                ds_target_pods = ds_data.status.desired_number_scheduled
                ds_ready_pods = ds_data.status.number_ready
                break
            else:
                ds_target_pods = 0
                ds_ready_pods = 0
        if (0 not in (ds_target_pods, ds_ready_pods)) and (
                ds_target_pods == ds_ready_pods):
            return True
        return False

    @classmethod
    def search_crd(cls, cluster_crds, crd_name):
        cls.__logger.info(
            "cluster_crds: %s, crd_name: %s", cluster_crds, crd_name)
        for i in cluster_crds.items:
            if crd_name in i.metadata.name:
                return True
        return False

    def run(self, **kwargs):
        self.start_time = time.time()
        self.result = 0
        total = 0
        passed = 0
        try:
            daemon_sets = self.appsv1.list_daemon_set_for_all_namespaces()
            if os.getenv("CNI_DAEMON_SETS"):
                for cni_ds in list(
                        os.getenv("CNI_DAEMON_SETS", "").split(',')):
                    total = total + 1
                    if self.search_cni(daemon_sets, cni_ds):
                        passed = passed + 1
            crds = self.apiv1ext.list_custom_resource_definition()
            if os.getenv("CNI_CRDS"):
                for crd_name in list(
                        os.getenv("CNI_CRDS", "").split(',')):
                    total = total + 1
                    if self.search_crd(crds, crd_name):
                        passed = passed + 1
            try:
                self.result = 100 * (passed / total)
                self.__logger.info("self.result: %s", self.result)
            except ZeroDivisionError:
                self.__logger.error("No test has been run")
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Error with checking CNIs:")
        self.stop_time = time.time()
