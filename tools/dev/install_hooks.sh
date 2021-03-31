#!/bin/bash

BASE=$(dirname $0)

cp $BASE/check.sh $BASE/../../.git/hooks/pre-commit
