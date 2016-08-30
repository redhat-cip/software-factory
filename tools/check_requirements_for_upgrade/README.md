Check Python requirements updates
=================================

This script parses a requirements.txt file associated with a python project and
checks with pypi whether a newer version of a given requirement is available or
not. If it is, tox is run with the latest requirement version to test its
compatibility with the project.

One last test run is done with every requirements that can be updated safely set
to their latest versions, to make sure there are no incompatibilities when
used altogether.

Usage
-----

ZUUL_PROJECT=/path/to/project ./check_requirements_for_updates.sh

or

./check_requirements_for_updates.sh path/to/requirements.txt
