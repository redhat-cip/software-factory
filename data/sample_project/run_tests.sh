#!/bin/bash

set -e

echo -e "\nFLAKE8 tests"
find . -iname "*.py" | xargs flake8
echo -e "\n"
