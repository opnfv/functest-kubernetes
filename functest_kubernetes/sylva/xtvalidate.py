#!/bin/python

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Class that integrates Validate into Xtesting.
"""

import json
import os
import traceback
import time
import validate  # pylint: disable=E0401
from xtesting.core import testcase  # pip install xtesting


class XtestingValidate(testcase.TestCase):
    """
    Integrates Validate into Xtesting.
    """

    # pylint: disable=R0912
    def run(self, **kwargs):
        # print(kwargs)
        self.start_time = time.time()
        # pylint: disable=R1702
        try:
            rj = None  # file to write results in JSON format
            os.makedirs(self.res_dir, exist_ok=True)
            try:
                #
                # must have args name for the name of test case
                test = kwargs["test"]
                #
                try:
                    debug = kwargs["debug"]
                except KeyError:
                    debug = False
                try:
                    label = kwargs["label"]
                except KeyError:
                    label = None
                try:
                    node = kwargs["node"]
                except KeyError:
                    node = None
                #
                # label = None for all labels
                # node = None for all nodes
                val = validate.Validate(
                    configfile=validate.CONFIGFILE, debug=debug, label=label,
                    node=node)
                #
                if val.ready:
                    val.run(test=test)
                with open(f'{self.res_dir}/result.json', 'w+',
                          encoding='utf-8') as rj:
                    json.dump(val.endresj, rj, indent=2)
                    rj.close()
                try:
                    res = 1
                    if len(val.endresj["stackValidation"]["testCases"]) == 0:
                        res = 0
                    else:
                        for tc in val.endresj["stackValidation"]["testCases"]:
                            # print(tc)
                            for n in tc["nodes"]:
                                if n["result"] == "false":
                                    res = 0
                    self.result = res
                    # self.result = 1
                except KeyError:
                    self.result = 0
            except KeyError:
                with open(f'{self.res_dir}/error.txt', 'w+',
                          encoding='utf-8') as error:
                    error.write(f"Error: no name or nonexistent test case\
 name given in args: {kwargs}")
                    error.close()
                if rj is not None:
                    rj.close()
                self.result = 0
        except (IOError, OSError, json.JSONDecodeError):
            print(f"Error: {traceback.format_exc()}")
            self.result = 0
        self.stop_time = time.time()


# main
if __name__ == "__main__":
    XtV = XtestingValidate()
    XtV.res_dir = "res"  # to avoid Permission denied: '/var/lib/xtesting'
    XtV.run(test="validateRT")
    print(XtV.result)
