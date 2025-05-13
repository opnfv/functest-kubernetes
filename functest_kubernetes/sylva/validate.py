#!/bin/python

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Python program with class that validates k8s features by using Daemonsets
in k8s folder.

Usage:
python validate.py [--debug] [--config=configfilename] [--test=testName]
    [--node=workernodename]
"""

import argparse
from json.decoder import JSONDecodeError
from datetime import datetime
import json
import sys
import time
import logging
import re
from kubernetes import client, config, utils  # pip install kubernetes
from kubernetes.client.rest import ApiException
from requests.exceptions import RequestException

CONFIGFILE = "config.json"


# pylint: disable=R0904
class Validate:
    """
    Class with all the functionality to create namespace, daemonsets and
    validate k8s features
    """
    # pylint: disable=too-many-instance-attributes

    endresj = {}  # Dictionary to hold result at the end be printed as JSON
    resj = endresj["stackValidation"] = {}

    def open_config(self, configfile):
        """
        Open configuration file or configure error
        """
        try:
            with open(configfile, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.resj["error"] = f"Config file {configfile} not found."
            self.ready = False
            return None
        except PermissionError:
            self.resj["error"] = \
                f"Permission denied when trying to read {configfile}."
            self.ready = False
            return None
        except JSONDecodeError as e:
            self.resj["error"] = \
                f"Invalid JSON in config file {configfile}: {e}"
            self.ready = False
            return None

    def load_config(self, s):
        """
        Load configuration into variables
        """
        self.ns_pause = s["namespacePause"]
        self.pod_pause = s["podPause"]
        self.directory = s["deployFiles"]["directory"]
        self.ns = s["podNamespace"]
        self.multi = s["deployFiles"]["multi"]["name"]
        self.huge2mi = s["deployFiles"]["huge2mi"]["name"]
        self.huge1gi = s["deployFiles"]["huge1gi"]["name"]
        self.reserve = s["deployFiles"]["reserve"]["name"]
        self.tunedrt = s["deployFiles"]["tunedrt"]["name"]
        self.show_timestamps = s["show"]["timeStamps"]
        self.show_description = s["show"]["description"]
        self.show_ra2spec = s["show"]["ra2Spec"]

    # label = test only labeled nodes, or None to test all
    # node = test only one worker node, or None to test all
    def __init__(self, configfile, debug, label, node):
        self.debug = debug
        self.d = self.open_config(configfile)
        self.load_config(self.d["script"])

        try:
            config.load_kube_config()
            self.v1 = client.CoreV1Api()
            self.cl = client.ApiClient()
        except config.config_exception.ConfigException as e:
            self.resj["error"] = f"Failed to load kube config: {e}"
            self.ready = False
            return

        n = []
        try:
            for ln in self.v1.list_node().items:
                nn = ln.metadata.name
                if label is None and (node is None or node == nn):
                    n.append(nn)
                else:
                    lk = list(label.keys())[0]
                    lv = list(label.values())[0]
                    lsk = list(ln.metadata.labels.keys())
                    lsv = list(ln.metadata.labels.values())
                    for i in range(len(ln.metadata.labels)):
                        if lk == lsk[i] and lv == lsv[i] and \
                                (node is None or node == nn):
                            n.append(nn)
        except ApiException as e:
            self.resj["error"] = f"Kubernetes API error: {e}"
            self.ready = False
            return

        if len(n) > 0:
            self.nodes = n
            self.ready = True
        else:
            self.ready = False
            if node is not None:
                self.resj["error"] = f"Cannot find node with name {node}"
            else:
                if label is not None:
                    self.resj["error"] = \
                        f"Cannot find node(s) with label {label}"

    # pylint: disable=W0311, R0912, R0915
    def run(self, test):
        """
        Runs test cases
        Arguments:
            test = run only that one test case, or None to run all
        """
        if not self.ready:
            return
        start_time = time.time()
        if test == "validateAll":
            test = None
        implemented_tests = {
            "validateAnuketProfileLabels",
            "validateLinuxDistribution",
            "validateKubernetesAPIs",
            "validateLinuxKernelVersion",
            "validateHugepages",
            "validateSMT",
            "validatePhysicalStorage",
            "validateStorageQuantity",
            "validateVcpuQuantity",
            "validateCPUPinning",
            "validateNFD",
            "validateSystemResourceReservation",
            "validateRT"
        }
        tests_with_multi_daemonset = {
            "validateSMT",
            "validatePhysicalStorage",
            "validateCPUPinning",
            "validateRT"
        }
        unimplemented_tests = {
            "validateSecurityGroups",
        }
        if test is None or test in implemented_tests:
            self.resj["testCases"] = []
        if test is None:
            self.create_namespace()
            if self.check_empty_namespace():
                self.create_daemonset(self.multi, True)
                self.create_daemonset(self.huge2mi, False)
                self.create_daemonset(self.huge1gi, False)
                self.create_daemonset(self.reserve, False)
                self.create_daemonset(self.tunedrt, True)
                self.validate_anuket_profile_labels()
                self.validate_linux_distribution()
                self.validate_kubernetes_apis()
                self.validate_linux_kernel_version()
                self.validate_smt()
                self.validate_hugepages()
                # here do all other tests
                self.validate_rt()
        if test in tests_with_multi_daemonset:
            self.create_namespace()
            if self.check_empty_namespace():
                self.create_daemonset(self.multi, True)
        if test == "validateAnuketProfileLabels":
            self.validate_anuket_profile_labels()
        if test == "validateLinuxDistribution":
            self.validate_linux_distribution()
        if test == "validateKubernetesAPIs":
            self.validate_kubernetes_apis()
        if test == "validateLinuxKernelVersion":
            self.validate_linux_kernel_version()
        if test == "validateHugepages":
            self.create_namespace()
            if self.check_empty_namespace():
                self.create_daemonset(self.huge2mi, False)
                self.create_daemonset(self.huge1gi, True)
                self.validate_hugepages()
        if test == "validateSMT":
            self.validate_smt()
        if test == "validatePhysicalStorage":
            self.validate_physical_storage()
        if test == "validateStorageQuantity":
            self.validate_storage_quantity()
        if test == "validateVcpuQuantity":
            self.validate_vcpu_quantity()
        if test == "validateCPUPinning":
            self.validate_cpu_pinning()
        if test == "validateNFD":
            self.validate_nfd()
        if test == "validateSystemResourceReservation":
            self.create_namespace()
            if self.check_empty_namespace():
                self.create_daemonset(self.reserve, True)
                self.validate_system_resource_reservation()
        if test == "validateRT":
            # create NS and multi are already done above
            self.create_daemonset(self.tunedrt, True)
            self.validate_rt()
        if test == "validateTSN":
            self.resj["error"] = "Current testcase validateTSN doesn't work \
with virtual networking."
        #
        # at the end delete namespace
        if test is None or test in tests_with_multi_daemonset or \
                test == "validateSystemResourceReservation" or \
                test == "validateHugepages":
            self.delete_namespace()
        if test in unimplemented_tests:
            self.resj["error"] = f"Testcase {test} not implemented."
        if test is not None and test not in implemented_tests and \
                test not in unimplemented_tests:
            self.resj["error"] = f"Cannot find testcase {test}."

        def time_to_datetime(t):
            """
            Convert a float (Unix timestamp) to a formatted string like
            "Mon Dec  2 20:17:31 UTC 2024".

            Args:
                t (float): Unix timestamp (seconds since the epoch).

            Returns:
                str: Formatted date and time string.
            """
            dt = datetime.utcfromtimestamp(t)
            return dt.strftime("%a %b %d %H:%M:%S UTC %Y")

        stop_time = time.time()
        if self.show_timestamps:
            self.resj["timeStamps"] = {}
            self.resj["timeStamps"]["startTime"] = \
                f"{time_to_datetime(start_time)}"
            self.resj["timeStamps"]["stopTime"] = \
                f"{time_to_datetime(stop_time)}"

    def create_namespace(self):
        """
        Creates the namespace if not already there.
        """
        try:
            namespaces = self.v1.list_namespace(_request_timeout=3)
            items = namespaces.items
            ns_exists = False
            for i in items:
                if i.metadata.name == self.ns:
                    ns_exists = True
            if not ns_exists:
                namespace = client.V1Namespace(metadata={'name': self.ns})
                self.v1.create_namespace(namespace)
        except ApiException as e:
            self.resj["error"] = f"Kubernetes API Exception: {e}"
        except RequestException as e:
            self.resj["error"] = f"Network Request Exception: {e}"
        time.sleep(self.ns_pause)

    def delete_namespace(self):
        """
        Deletes namespace.
        """
        self.v1.delete_namespace(f"{self.ns}")  # doesn't wait

    def check_empty_namespace(self):
        """
        Checks if namespace is empty.
        """
        r = self.v1.list_pod_for_all_namespaces(watch=False)
        for i in r.items:
            if i.metadata.namespace == self.ns:
                print(f"i.metadata = {i.metadata}")
                self.resj["error"] = f"There are pods already running in \
namespace {self.ns}. Wait after previous test, or manually delete them (like \
with kubectl delete ns {self.ns})."
                return False
        return True

    def create_daemonset(self, name, with_sleep):
        """
        Creates daemonset.
        """
        utils.create_from_yaml(self.cl, f"{self.directory}/{name}.yaml")
        if with_sleep:
            time.sleep(self.pod_pause)
        # now = time.time()
        # while True:
        #    some_dont_run = False
        #    r = self.v1.list_pod_for_all_namespaces(watch=False)
        #    for i in r.items:
        #        if i.metadata.namespace == self.ns and \
        #            i.metadata.name.startswith("test-ptphwclock-"):
        #            if i.status.phase != "Running":
        #                some_dont_run = True
        #    if not some_dont_run or time.time() - now > self.pod_pause:
        #        break
        #    time.sleep(1)

    def add_begin(self, name):  # returns testcase node in result JSON
        """
        Sets initial parts of JSON result.
        """
        description = ""
        ra2spec = ""
        for tc in self.d["testCases"]:
            if tc["name"] == name:
                description = tc["description"]
                ra2spec = tc["ra2Spec"]
        tcjn = {"name": f"{name}"}  # testcase JSON node
        self.resj["testCases"].append(tcjn)
        if self.show_description:
            tcjn["description"] = description
        if self.show_ra2spec:
            tcjn["ra2Spec"] = ra2spec
        tcjn["nodes"] = []
        return tcjn

    def validate_anuket_profile_labels(self):
        """
        Test case to validate Anuket profile labels.
        """
        #
        # testcase JSON node
        tcjn = self.add_begin("validateAnuketProfileLabels")
        #
        label_key = None
        label_values = None
        for tc in self.d["testCases"]:
            if tc["name"] == "validateAnuketProfileLabels":
                label_key = tc["anuketProfileLabelKey"]
                label_values = tc["anuketProfileLabelValues"]
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            res = False
            d = ""
            try:
                labels = self.v1.read_node(n).metadata.labels
                value = labels.get(label_key)
                res = value in label_values
                if res:
                    d = f"{label_key}={value}"
                else:
                    d = f"No label {label_key}"
            except client.exceptions.ApiException as e:
                self.resj["error"] = f"Error fetching node details: {e}"
                cwn["result"] = "false"
            cwn["result"] = str(res).lower()
            if self.debug:
                cwn["debug"] = d

    # rework to check for rpm/deb and not osImage?
    def validate_linux_distribution(self):
        """
        Test case to validate Linux distribution Red Hat, CentOS, Ubuntu...
        """
        tcjn = self.add_begin("validateLinuxDistribution")
        distro_names = ""
        for tc in self.d["testCases"]:
            if tc["name"] == "validateLinuxDistribution":
                distro_names = tc["distroNames"]
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            try:
                os_image = self.v1.read_node(n).status.node_info.os_image
                res = False
                for d in distro_names:
                    if d["name"] in os_image:
                        res = True
                cwn["result"] = str(res).lower()
                if self.debug:
                    cwn["debug"] = f"linux={os_image}"
            except client.exceptions.ApiException as e:
                self.resj["error"] = f"Error fetching node details: {e}"
                cwn["result"] = "false"

    def validate_kubernetes_apis(self):
        """
        Test case to validate Kubernetes APIs alpha and beta.
        """
        tcjn = self.add_begin("validateKubernetesAPIs")
        exceptions = ""
        for tc in self.d["testCases"]:
            if tc["name"] == "validateKubernetesAPIs":
                exceptions = tc["exceptions"]
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
        api_resources = client.ApisApi(self.cl).get_api_versions()
        res = True
        d = ""
        for g in api_resources.groups:
            for v in g.versions:
                if "alpha" in v.version or "beta" in v.version:
                    in_exceptions = False
                    if d != "":
                        d += ", "
                    for e in exceptions:
                        if e["name"] in v.group_version:
                            in_exceptions = True
                            d += "exception="
                    d += v.group_version
                    if not in_exceptions:
                        res = False
        cwn["result"] = str(res).lower()
        if self.debug:
            cwn["debug"] = d

    def validate_linux_kernel_version(self):
        """
        Test case to validate Linux kernel version.
        """
        tcjn = self.add_begin("validateLinuxKernelVersion")
        min_major = None
        min_minor = None
        for tc in self.d["testCases"]:
            if tc["name"] == "validateLinuxKernelVersion":
                min_major = tc["minMajor"]
                min_minor = tc["minMinor"]
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            d = ""
            try:
                kernel_version = \
                    self.v1.read_node(n).status.node_info.kernel_version
                major = int(kernel_version.split(".")[0])
                minor = int(kernel_version.split(".")[1])
                res = False
                if major > min_major:
                    res = True
                if major == min_major and minor >= min_minor:
                    res = True
                d = f"kernel={kernel_version}"
            except client.exceptions.ApiException as e:
                self.resj["error"] = f"Error fetching node details: {e}"
                cwn["result"] = "false"
            cwn["result"] = str(res).lower()
            if self.debug:
                cwn["debug"] = d

    # pylint: disable=R0914
    def validate_hugepages(self):
        """
        Test to validate hugepages.
        """
        tcjn = self.add_begin("validateHugepages")
        types = []
        for tc in self.d["testCases"]:
            if tc["name"] == "validateHugepages":
                types = tc["types"]
        pods = self.v1.list_pod_for_all_namespaces(watch=False)
        # pylint: disable=R1702
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            res = False
            s = 0
            alloc = {}
            d = ""
            for t in types:
                tn = t["name"]
                a = int(re.sub(r'[^\d]', '',
                        self.v1.read_node(n).status.allocatable.get(
                            f"hugepages-{tn}")))
                alloc[f"{tn}"] = a
                s += a
                if d != "":
                    d += ", "
                d += f"alloc_{tn}={a}"
            if s > 0:
                for p in pods.items:
                    if (p.metadata.namespace == self.ns and (
                            p.metadata.name.startswith(
                                f"test-{self.huge2mi}-") or
                            p.metadata.name.startswith(
                                f"test-{self.huge1gi}-")
                            )):
                        log = self.v1.read_namespaced_pod_log(
                            namespace=self.ns, name=p.metadata.name)
                        hugepages = 0
                        nr_hugepages = 0
                        meminfo_hugepages_free = 0
                        mount_dev_hugepages = 0
                        for log_line in log.split("\n"):
                            if log_line.startswith("hugepages="):
                                hugepages = int(log_line.split("=")[1])
                            if log_line.startswith("nr_hugepages"):
                                nr_hugepages = int(log_line.split("=")[1])
                            if log_line.startswith("meminfo_HugePages_Free"):
                                meminfo_hugepages_free = int(
                                    log_line.split("=")[1])
                            if log_line.startswith("mount_dev_hugepages"):
                                mount_dev_hugepages = int(
                                    log_line.split("=")[1])
                            if hugepages > 0:
                                res = True
                        d += f", nr_hugepages={nr_hugepages}, \
meminfo_hugepages_free={meminfo_hugepages_free}, \
mount_dev_hugepages={mount_dev_hugepages}"
            cwn["result"] = str(res).lower()
            if self.debug:
                cwn["debug"] = d

    def validate_smt(self):
        """
        Test case to validate SMT by checking /proc/cpuinfo.
        Assumes either no hypervisor or that hypervisor is not emulating SMT.
        """
        tcjn = self.add_begin("validateSMT")
        pods = self.v1.list_pod_for_all_namespaces(watch=False)
        # pylint: disable=R1702
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            res = False
            d = ""
            for p in pods.items:
                if p.metadata.namespace == self.ns and \
                        p.metadata.name.startswith(f"test-{self.multi}-"):
                    log = self.v1.read_namespaced_pod_log(
                        namespace=self.ns, name=p.metadata.name)
                    vcpus = None
                    threadspercore = None
                    corespersocket = None
                    sockets = None
                    for log_line in log.split("\n"):
                        if log_line.startswith("vcpus="):
                            vcpus = int(log_line.split("=")[1])
                            d += f"vcpus={vcpus}"
                        if log_line.startswith("threadspercore="):
                            threadspercore = int(log_line.split("=")[1])
                            if d != "":
                                d += ", "
                            d += f"threadspercore={threadspercore}"
                        if log_line.startswith("corespersocket="):
                            corespersocket = int(log_line.split("=")[1])
                            if d != "":
                                d += ", "
                            d += f"corespersocket={corespersocket}"
                        if log_line.startswith("sockets="):
                            sockets = int(log_line.split("=")[1])
                            if d != "":
                                d += ", "
                            d += f"sockets={sockets}"
                    if vcpus is not None and threadspercore is not None \
                            and corespersocket is not None \
                            and sockets is not None:
                        if vcpus == sockets * corespersocket * threadspercore:
                            res = True
            cwn["result"] = str(res).lower()
            if self.debug:
                cwn["debug"] = d

    def validate_physical_storage(self):
        """
        Test case to validate if physical storage device type is SSD.
        Assumes either no hypervisor or that hypervisor is not masking physical
            storage device type.
        """
        tcjn = self.add_begin("validatePhysicalStorage")
        pods = self.v1.list_pod_for_all_namespaces(watch=False)
        # pylint: disable=R1702
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            res = False
            d = ""
            for p in pods.items:
                if p.metadata.namespace == self.ns and \
                        p.metadata.name.startswith(f"test-{self.multi}-"):
                    log = self.v1.read_namespaced_pod_log(
                        namespace=self.ns, name=p.metadata.name)
                    res = False
                    pcidevs = []
                    for log_line in log.split("\n"):
                        if log_line.startswith("pcidev="):
                            #
                            # 9: skips device ID
                            pcidev = log_line.split("=")[1][9:]
                            #
                            if "SSD" in pcidev:
                                res = True
                            if pcidev not in pcidevs:
                                pcidevs.append(pcidev)
                    for dev in pcidevs:
                        if d != "":
                            d += ", "
                        d += dev
            cwn["result"] = str(res).lower()
            if self.debug:
                cwn["debug"] = d

    def validate_storage_quantity(self):
        """
        Test case to validate storage is > set GB.
        """
        tcjn = self.add_begin("validateStorageQuantity")
        limit = None
        for tc in self.d["testCases"]:
            if tc["name"] == "validateStorageQuantity":
                limit = tc["limit"]
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            res = False
            d = ""
            try:
                storage_bytes = int(
                    self.v1.read_node(n).status.allocatable.get(
                        "ephemeral-storage"))
                storage_gib = int(storage_bytes / (1024 ** 3))
                if limit is not None and storage_gib >= limit:
                    res = True
                d = f"ephemeral_storage={storage_gib}GiB"
            except client.exceptions.ApiException as e:
                self.resj["error"] = f"Error fetching node details: {e}"
                cwn["result"] = "false"
            cwn["result"] = str(res).lower()
            if self.debug:
                cwn["debug"] = d

    def validate_vcpu_quantity(self):
        """
        Test case to validate vCPUs are > set minimum.
        """
        tcjn = self.add_begin("validateVcpuQuantity")
        limit = None
        for tc in self.d["testCases"]:
            if tc["name"] == "validateVcpuQuantity":
                limit = tc["limit"]
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            res = False
            d = ""
            try:
                vcpus = int(self.v1.read_node(n).status.capacity["cpu"])
                if limit is not None and vcpus >= limit:
                    res = True
                d = f"cpu={vcpus}"
            except client.exceptions.ApiException as e:
                self.resj["error"] = f"Error fetching node details: {e}"
                cwn["result"] = "false"
            cwn["result"] = str(res).lower()
            if self.debug:
                cwn["debug"] = d

    def validate_cpu_pinning(self):
        """
        Test case to validate if CPU pinning is activated via kubelet static
        CPU policy.
        """
        tcjn = self.add_begin("validateCPUPinning")
        pods = self.v1.list_pod_for_all_namespaces(watch=False)
        # pylint: disable=R1702
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            res = False
            d = ""
            for p in pods.items:
                if p.metadata.namespace == self.ns and \
                        p.metadata.name.startswith(f"test-{self.multi}-"):
                    log = self.v1.read_namespaced_pod_log(
                        namespace=self.ns, name=p.metadata.name)
                    cpusetlimited = None
                    allrange = None
                    cpusetcpus = None
                    for log_line in log.split("\n"):
                        if log_line.startswith("cpusetlimited="):
                            cpusetlimited = int(log_line.split("=")[1])
                        if log_line.startswith("allrange="):
                            allrange = log_line.split("=")[1]
                            d += f"allrange={allrange}"
                        if log_line.startswith("cpusetcpus="):
                            cpusetcpus = log_line.split("=")[1]
                            if d != "":
                                d += ", "
                            d += f"cpusetcpus={cpusetcpus}"
                    if cpusetlimited == 1:
                        res = True
            cwn["result"] = str(res).lower()
            if self.debug:
                cwn["debug"] = d

    def validate_nfd(self):
        """
        Test if there are enough NFV labels.
        """
        tcjn = self.add_begin("validateAnuketProfileLabels")
        limit = None
        for tc in self.d["testCases"]:
            if tc["name"] == "validateNFD":
                limit = tc["limit"]
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            res = False
            d = ""
            try:
                labels = self.v1.read_node(n).metadata.labels
                if len(labels) >= limit:
                    res = True
                d = f"labels={len(labels)}"
            except client.exceptions.ApiException as e:
                self.resj["error"] = f"Error fetching node details: {e}"
                cwn["result"] = "false"
            cwn["result"] = str(res).lower()
            if self.debug:
                cwn["debug"] = d

    def validate_system_resource_reservation(self):
        """
        Test if system resources were reserved.
        """
        tcjn = self.add_begin("validateSystemResourceReservation")
        checks = []
        for tc in self.d["testCases"]:
            if tc["name"] == "validateSystemResourceReservation":
                checks = tc["checks"]
        pods = self.v1.list_pod_for_all_namespaces(watch=False)
        # pylint: disable=R1702
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            res = False
            d = "not found"
            for p in pods.items:
                if p.metadata.namespace == self.ns and \
                        p.metadata.name.startswith(f"test-{self.reserve}-"):
                    log = self.v1.read_namespaced_pod_log(
                        namespace=self.ns, name=p.metadata.name)
                    res = False
                    cmd = ""
                    for log_line in log.split("\n"):
                        if log_line.startswith("ps-ef="):
                            cmd = log_line[6:]  # 6: skips "ps-ef="
                            for ch in checks:
                                if ch["process"] in cmd:
                                    if f'--{ch["flag"]}' in cmd:
                                        res = True
                                    if d == "not found":
                                        d = f"command={cmd}"
                                    if d != "":
                                        d += f", {cmd}"
            cwn["result"] = str(res).lower()
            if self.debug:
                cwn["debug"] = d

    # pylint: disable=R0912, R0914, R0915
    def validate_rt(self):
        """
        Test case to validate RT settings:
        - all CPUs same frequency
        - kernel RT
        - tuned RT settings
        """
        tcjn = self.add_begin("validateRT")  # testcase JSON node
        kernel_names = ""
        preempt_name = ""
        for tc in self.d["testCases"]:
            if tc["name"] == "validateRT":
                kernel_names = tc["kernelNames"]
                preempt_name = tc["preemptName"]
        pods = self.v1.list_pod_for_all_namespaces(watch=False)
        # pylint: disable=R1702
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            node_with_multi_pod = False  # for kernelrt
            node_with_tunedrt_pod = False
            res_cpupower = False
            res_kernelrt = False
            res_tunedrt = False
            debug_cpupower = ""
            debug_tunedrt = ""
            for p in pods.items:
                if p.metadata.namespace == self.ns and \
                        p.metadata.name.startswith(f"test-{self.multi}-"):
                    node_with_multi_pod = True
                    log = self.v1.read_namespaced_pod_log(
                        namespace=self.ns, name=p.metadata.name)
                    #
                    # cpupower frequency-info | grep "CPUs which run at the
                    #   same hardware frequency"
                    shf = False
                    #
                    for log_line in log.split("\n"):
                        if log_line.startswith("cpussamehwfreq="):
                            if "NotAvailable" in log_line:
                                shf = False
                            else:
                                shf = True
                            debug_cpupower = log_line
                    res_cpupower = shf
                    log = self.v1.read_namespaced_pod_log(
                        namespace=self.ns, name=p.metadata.name)
                    knr = False  # kernel with -rt, -realtime
                    per = False  # PREEMPT_RT
                    skr = False  # /sys/kernel/realtime
                    pcr = False  # /proc/cmdline with BOOT_IMAGE=*/*-realtime
                    debug_kernelrt = ""
                    for log_line in log.split("\n"):
                        if "unamerv=" in log_line:
                            for kn in kernel_names:
                                if f'-{kn["name"]}' in log_line:
                                    knr = True
                            if f" {preempt_name} " in log_line:
                                per = True
                            debug_kernelrt = log_line
                        if "syskernelrealtime=" in log_line:
                            _, l2 = log_line.split("syskernelrealtime=", 1)
                            if l2 == "1":
                                skr = True
                            debug_kernelrt += "; " + log_line
                        if log_line.startswith("proccmdline="):
                            _, l2 = log_line.split("proccmdline=", 1)
                            for w in l2.split(" "):
                                if w.startswith("BOOT_IMAGE="):
                                    for kn in kernel_names:
                                        if f'-{kn["name"]}' in log_line:
                                            pcr = True
                            debug_kernelrt += "; " + log_line
                    res_kernelrt = knr and per and skr and pcr
                if p.metadata.namespace == self.ns and \
                        p.metadata.name.startswith(
                            f"test-{self.tunedrt}-") and \
                        p.status.phase == "Running":
                    node_with_tunedrt_pod = True
                    log = self.v1.read_namespaced_pod_log(
                        namespace=self.ns, name=p.metadata.name)
                    # grep "static tuning from profile"
                    #   /var/log/tuned/tuned.log | tail -1 | grep -c realtime
                    trt = False
                    for log_line in log.split("\n"):
                        if "tunedlogrealtime=" in log_line:
                            _, l2 = log_line.split("tunedlogrealtime=", 1)
                            if l2 == "1":
                                trt = True
                        if "tunedlogstatictuning=" in log_line:
                            debug_tunedrt = log_line
                    res_tunedrt = trt
            # node_with_tunedrt_pod won't schedule if it cannot mount tuned
            # log file, but still show debug for kernelrt and cpupower
            if node_with_multi_pod:
                if self.debug:
                    cwn["debug"] = f"{debug_cpupower}; {debug_kernelrt}"
            if node_with_multi_pod and node_with_tunedrt_pod:
                res = res_cpupower and res_kernelrt and res_tunedrt
                cwn["result"] = str(res).lower()
                if self.debug:
                    cwn["debug"] = \
                        f"{debug_cpupower}; {debug_kernelrt}; {debug_tunedrt}"
            else:
                cwn["result"] = "false"
                e = "Cannot find pods "
                if not node_with_multi_pod:
                    e += f"test-{self.multi} "
                if not node_with_tunedrt_pod:
                    e += f"test-{self.tunedrt}"
                cwn["error"] = e


# pylint: disable=W0105
'''
    def validateTSN(self):
        name = "validateTSN"
        tcjn = self.add_begin(name)
        for tc in self.d["testCases"]:
            if tc["name"] == name:
                kernel_names = tc["dev"]
        pods = self.v1.list_pod_for_all_namespaces(watch=False)
        res_ptphwclock = False
        for n in self.nodes:
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            node_with_ptphwclock_pod = False
            for p in pods.items:
                if p.metadata.namespace == self.ns and \
                        p.metadata.name.startswith(f"test-{PTPHWCLOCK}-"):
                    node_with_ptphwclock_pod = True
                    log = self.v1.read_namespaced_pod_log(
                        namespace=self.ns, name=p.metadata.name)
                    phc = False  # ethtool -T eth0 | grep PTP
                    debug_ptphwclock = ""
                    for l in log.split("\n"):
                        if "ptphwclock=" in l:
                            if f'none' in l:
                                shf = False
                            else:
                                shf = True
                            debug_ptphwclock = l
                    res_ptphwclock = phc
            if node_with_ptphwclock_pod:
                res = res_ptphwclock
                cwn["result"] = str(res).lower()
                if self.DEBUG:
                    cwn["debug"] = debug_ptphwclock
            else:
                cwn["result"] = "false"
                cwn["error"] = f"Cannot find pod test-{self.PTPHWCLOCK}"
'''
# pylint: enable=W0105


# main
if __name__ == "__main__":
    # pylint: disable=C0103
    cf = CONFIGFILE
    debug_flag = False
    test_flag = None  # if only single test case should be run
    label_flag = None  # label: if only labeled nodes should be tested
    node_flag = None  # node: if only single node should be tested
    # pylint: enable=C0103
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug", dest="debug", help="Debug", action="store_true")
    parser.add_argument(
        "--config", dest="config_filename", help="Config file name")
    parser.add_argument("--test", dest="test", help="Test case name")
    parser.add_argument("--label", dest="label", help="Node label")
    parser.add_argument("--node", dest="node", help="Node name")
    parser.add_argument(
        "--delete-ns", dest="delete", help="Delete NS", action="store_true")
    args = parser.parse_args(sys.argv[1:])
    if isinstance(args, argparse.Namespace):
        if args.debug:
            debug_flag = True  # pylint: disable=C0103
        if args.config_filename is not None:
            cf = args.config_filename
        if args.test is not None:
            test_flag = args.test
        if args.label is not None:
            label_flag = args.label
        if args.node is not None:
            node_flag = args.node
    val = Validate(cf, debug_flag, label_flag, node_flag)
    if args.delete:
        val.delete_namespace()
        logger = logging.getLogger(__name__)
        logger.info("Deleted namespace %s", val.ns)
    elif val.ready:
        val.run(test_flag)
        print(json.dumps(val.endresj, indent=2))
