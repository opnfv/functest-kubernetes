#!/usr/bin/env python

# pylint: disable=missing-docstring

import time
import sys
from kubernetes import client, config
from xtesting.core import testcase


class CniInstallation(testcase.TestCase):

    def run(self, **kwargs):
        self.start_time = time.time()
        try:
            config.load_kube_config()
            kubectl = client.AppsV1Api()
            cni_ds = kwargs.get('cni_ds')

            cluster_daemon_sets = kubectl.list_daemon_set_for_all_namespaces()
            for i in cluster_daemon_sets.items:
                if cni_ds in i.metadata.name:
                    ds_name = i.metadata.name
                    ds_ns = i.metadata.namespace
                    ds_data = kubectl.read_namespaced_daemon_set(
                        namespace=ds_ns, name=ds_name)
                    ds_target_pods = ds_data.status.desired_number_scheduled
                    ds_ready_pods = ds_data.status.number_ready
                    break
                else:
                    ds_target_pods = 0
                    ds_ready_pods = 0

            if (0 not in (ds_target_pods, ds_ready_pods)) and (
                    ds_target_pods == ds_ready_pods):
                self.result = 100
            else:
                self.result = 0

        except Exception:  # pylint: disable=broad-except
            print("Unexpected error:", sys.exc_info()[0])
            self.result = 0
        self.stop_time = time.time()


class CrdCreation(testcase.TestCase):

    def run(self, **kwargs):
        self.start_time = time.time()
        try:
            config.load_kube_config()
            kubectl = client.ApiextensionsV1Api()
            crd_name = kwargs.get('crd_name')

            cluster_crds = kubectl.list_custom_resource_definition()
            for i in cluster_crds.items:
                if crd_name in i.metadata.name:
                    crd = i.metadata.name
                    break
                else:
                    crd = ""

            if crd == crd_name:
                self.result = 100
            else:
                self.result = 0

        except Exception:  # pylint: disable=broad-except
            print("Unexpected error:", sys.exc_info()[0])
            self.result = 0
        self.stop_time = time.time()
