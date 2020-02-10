#!/bin/bash

echo "------------------------------------------------------------------------"
echo "-----------------  Test if K8S is CIS compliant   ----------------------"
echo "------------------------------------------------------------------------"

code=0

CIS_VERSION=${CIS_VERSION:-1.4}
echo "Running CIS test case version ${CIS_VERSION}"
kube-bench master --benchmark cis-${CIS_VERSION} > cis_full_test.txt
cat cis_full_test.txt | grep "\[FAIL]" > cisK8s.txt

if [ -s cisK8s.txt ]
then
   code=1
   nb_errors=`cat cisK8s.txt | wc -l`
   echo "Test FAIL: $nb_errors assertions not passed"
   cat cis_full_test.txt
else
  echo "Test PASS: Kubernetes Deployment is CIS compatible"
fi

exit $code
