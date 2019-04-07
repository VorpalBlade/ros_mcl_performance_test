#!/bin/bash

if [[ $# -ne 2 ]]; then
	echo "Usage: $0 <path-to-quickmcl-binary> <path-to-amcl-binary>"
	echo ""
	echo "Remember to start roscore before as well as external laser processing"
	exit 1
fi

_paths=(
	--quickmcl-path "$1"
	--amcl-path "$2"
)

echo "# QuickMCL external laser"

for i in {500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000}; do
	./run_tests.py quickmcl --quickmcl-external-laser -s 10 -r 5 -p $i "${_paths[@]}"
done

echo "# QuickMCL internal laser"

for i in {500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000}; do
	./run_tests.py quickmcl -s 10 -r 5 -p $i "${_paths[@]}"
done

echo "# AMCL"

for i in {500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000}; do
	./run_tests.py amcl -s 10 -r 5 -p $i "${_paths[@]}"
done
