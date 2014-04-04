#!/bin/bash

set -x

export SF_PREFIX=tests
(cd lxc; ./bootstrap-lxc.sh clean)
nosetests -v ./tests
RET=$?
(cd lxc; ./bootstrap-lxc.sh clean)
exit $RET
