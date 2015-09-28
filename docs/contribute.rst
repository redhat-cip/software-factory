.. toctree::

Contributing to Software Factory
================================

How can I help?
---------------

Thanks for asking.

The easiest way to get involved is to join us on IRC: #softwarefactory channel on Freenode.

User stories and bug tracker is available here: http://softwarefactory-project.io/redmine/projects/software-factory/issues

Prepare a development environment
---------------------------------

To get a development environment and a Software Factory up and running,
you need access to a CentOS 7 and execute:

.. code-block:: bash

 $ sudo yum install -y libvirt-daemon-lxc git tmux curl python-devel ...
 $ git clone http://softwarefactory-project.io/r/software-factory
 $ cd software-factory
 $ ./fetch_image.sh


How to run the tests locally
----------------------------

There are four kinds of tests:

* Unit tests
* Functional tests
* Upgrade tests
* Backup tests

Before sending a patch to the upstream softwarefactory code, it's better
to run functional and unit tests locally first:

.. code-block:: bash

  $ ./run_tests.sh               # unittests
  $ ./run_functional-tests.sh    # functional tests

Two reference architectures are currently supported and tested with functional,
backup and restore tests: 1node-allinone and 2nodes-jenkins

.. code-block:: bash

  $ ./run_functional-tests.sh 1node-allinone          # functional tests
  $ ./run_functional-tests.sh 2nodes-jenkins upgrade  # upgrade tests
  $ ./run_functional-tests.sh 1node-allinone backup   # backup tests

The functional tests will start LXC container(s) on the local VM to simulate
as close as possible a real deployment. Setting the DEBUG=1 environment variable
tells the script to keep the deployment running. If not set the deployment
will be destroyed (LXC containers will be stopped).


How to develop and/or run a specific functional tests
-----------------------------------------------------

Functional tests needs access to the keys and configuration of the deployment.
First you need to copy the sf-bootstrap-data/ from the managesf node.

.. code-block:: bash

  $ rsync -a root@tests.dom:sf-bootstrap-data/ sf-bootstrap-data/
  $ nosetests --no-byte-compile -s -v tests/functional

Tips: ::

 * '-s' enables the use of 'import pdb; pdb.set_trace()' within a test
 * Within a test insert 'from nose.tools import set_trace; set_trace()' to add breakpoint in nosetests
 * '--no-byte-compile' makes sure no .pyc are run
 * you can use file globs to select specific tests: [...]/tests/functional/*zuul*
 * in order to have passwordless ssh and dns configuration, here is a convenient .ssh/config file:

.. code-block:: none

  Host tests.dom
    StrictHostKeyChecking no
    User root
    Hostname 192.168.135.101


How to contribute
-----------------

* Connect to http://softwarefactory-project.io/
* Register your public SSH key on your account. Have a look to: :ref:`Adding public key`.
* Check the bugtracker and the pending reviews
* Submit your change

.. code-block:: bash

  $ cd /srv/software-factory
  $ git-review -s # only relevant the first time to init the git remote
  $ git checkout -b"my-branch"
  $ # Hack the code, create a commit on top of HEAD ! and ...
  $ git review # Summit your proposal on softwarefactory-project.io

Have a look to http://softwarefactory-project.io/r/ where you will find the patch
you have just submitted. Automatic tests are run against it and Jenkins/Zuul will
report a status as comments on the Gerrit page related to your patch. You can
also check http://softwarefactory-project.io/zuul/ to follow the test process.

Note that Software Factory is developed using Software Factory. That means that you can
contribute to SF in the same way you would contribute to any other project hosted
on SF: :ref:`contribute`.
