#!/usr/bin/env python

# pylint: disable=missing-docstring

import logging
import os
import time

from kubernetes import client
from kubernetes import config
import prettytable
from xtesting.core import testcase


class CniSmoke(testcase.TestCase):
    # pylint: disable=too-many-instance-attributes

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_log_name = 'functest-kubernetes.log'
        self.output_debug_log_name = 'functest-kubernetes.debug.log'
        config.load_kube_config()
        self.appsv1 = client.AppsV1Api()
        self.apiv1ext = client.ApiextensionsV1Api()

    def check_requirements(self):
        if (not os.getenv("CNI_DAEMON_SETS") and not os.getenv("CNI_CRDS")):
            self.is_skipped = True
            self.__logger.warning(
                "Please set CNI_DAEMON_SETS or CNI_CRDS in env")

    def search_cni(self, cluster_daemon_sets, cni_ds):
        self.__logger.debug(
            "cluster_daemon_sets: %s, cni_ds: %s",
            cluster_daemon_sets, cni_ds)
        detail = {
            'type': 'daemon_set',
            'name': cni_ds,
            'matched': None,
            'namespace': None,
            'desired': 0,
            'ready': 0,
            'result': 'FAIL',
        }
        for i in cluster_daemon_sets.items:
            if cni_ds in i.metadata.name:
                ds_name = i.metadata.name
                ds_ns = i.metadata.namespace
                ds_data = self.appsv1.read_namespaced_daemon_set(
                    namespace=ds_ns, name=ds_name)
                self.__logger.debug("ds_data: %s", ds_data)
                ds_target_pods = ds_data.status.desired_number_scheduled
                ds_ready_pods = ds_data.status.number_ready
                detail.update({
                    'matched': ds_name,
                    'namespace': ds_ns,
                    'desired': ds_target_pods,
                    'ready': ds_ready_pods,
                })
                self.__logger.info(
                    "CNI daemon set %s matched %s/%s: %s/%s pods ready",
                    cni_ds, ds_ns, ds_name, ds_ready_pods, ds_target_pods)
                break
        if (0 not in (detail['desired'], detail['ready'])) and (
                detail['desired'] == detail['ready']):
            self.__logger.info("CNI daemon set %s: PASS", cni_ds)
            detail['result'] = 'PASS'
        else:
            self.__logger.warning("CNI daemon set %s: FAIL", cni_ds)
        return detail

    @classmethod
    def search_crd(cls, cluster_crds, crd_name):
        cls.__logger.debug(
            "cluster_crds: %s, crd_name: %s", cluster_crds, crd_name)
        detail = {
            'type': 'crd',
            'name': crd_name,
            'matched': None,
            'result': 'FAIL',
        }
        for i in cluster_crds.items:
            if crd_name in i.metadata.name:
                detail['matched'] = i.metadata.name
                detail['result'] = 'PASS'
                cls.__logger.info(
                    "CNI CRD %s matched %s: PASS", crd_name, i.metadata.name)
                break
        else:
            cls.__logger.warning("CNI CRD %s: FAIL", crd_name)
        return detail

    def run(self, **kwargs):
        self.start_time = time.time()
        self.result = 0
        total = 0
        passed = 0
        checks = []
        try:
            daemon_sets = self.appsv1.list_daemon_set_for_all_namespaces()
            if os.getenv("CNI_DAEMON_SETS"):
                for cni_ds in list(
                        os.getenv("CNI_DAEMON_SETS", "").split(',')):
                    total = total + 1
                    detail = self.search_cni(daemon_sets, cni_ds)
                    checks.append(detail)
                    if detail['result'] == 'PASS':
                        passed = passed + 1
            crds = self.apiv1ext.list_custom_resource_definition()
            if os.getenv("CNI_CRDS"):
                for crd_name in list(
                        os.getenv("CNI_CRDS", "").split(',')):
                    total = total + 1
                    detail = self.search_crd(crds, crd_name)
                    checks.append(detail)
                    if detail['result'] == 'PASS':
                        passed = passed + 1
            try:
                self.result = 100 * (passed / total)
                self.__logger.info(
                    "self.result: %s (%s/%s CNI checks passed)",
                    self.result, passed, total)
            except ZeroDivisionError:
                self.__logger.error("No test has been run")
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Error with checking CNIs:")
        self.details = {'checks': checks}
        if checks:
            msg = prettytable.PrettyTable(
                header_style='upper', padding_width=5,
                field_names=['type', 'name', 'matched', 'namespace',
                             'desired', 'ready', 'result'])
            for detail in checks:
                msg.add_row([
                    detail['type'], detail['name'],
                    detail.get('matched') or '-',
                    detail.get('namespace') or '-',
                    detail.get('desired', '-'), detail.get('ready', '-'),
                    detail['result']])
            self.__logger.info("\n\n%s\n", msg.get_string())
        self.stop_time = time.time()
