.. toctree::

Contributing to Software Factory
================================

How can I help?
---------------

Thanks for asking. Let's find a place for you!

First you should join our communication forums:

* Join us on IRC: You can talk to us directly in the #softwarefactory channel
  on Freenode.
* Read the official Software Factory documentation. You can access it there:
  http://softwarefactory.enovance.com/_docs/
* A good way to start contributing is to report any errors or unclear
  parts in the documentation.

To report those problems feel free to contact us on Freenode or even create
a bug report on the bugtracker: http://softwarefactory.enovance.com/_redmine/projects/software-factory

Then you should deploy your own softwarefactory. You can use _`sfstack`
to simplify the installation of the development environment.

Prepare a development environment with sfstack
----------------------------------------------

Sfstack is a suite of scripts that you can download from our public
softwarefactory instance. The idea is to install a Ubuntu 14.04 in a
VM somewhere, and start the *sfinstall.sh* script in order to prepare
a development environment.

.. code-block:: bash

 $ git clone http://softwarefactory.enovance.com/r/sfstack
 $ cd sfstack
 $ sudo ./sfinstall.sh

The *sfinstall.sh* script will install all the dependencies needed and fetch the
softwarefactory source code. Note that we also use this project to build our
Jenkins slaves to run softwarefactory functional tests.

After a successful run of *sfinstall.sh* you will find the
cloned directory of software-factory in /srv. Please jump into it.

Then you can fetch pre-built trees (:ref:`fetchprebuilt`) and follow (:ref:`lxcdeploy`)
to learn how to start a local softwarefactory, but skip the dependencies
download instructions as the *sfinstall.sh* script already done that for you.

How to run the tests locally
----------------------------

We have three kinds of tests that are: ::

 * Unit tests
 * Functional tests against a LXC deployment
 * Functional tests against an OpenStack HEAT deployment

Before sending a patch to the upstream softwarefactory code, we advise
you to run the LXC tests and unittests.

.. code-block:: bash

  $ cd /srv/software-factory
  $ ./run_tests.sh # unittests
  $ DEBUG=1 ./run_functional-tests.sh # functional tests

The functional tests will start LXC containers on the local VM to simulate
as close as possible a real deployment. Setting the DEBUG environment variable
to something tells the script to let the deployment up. If not set the deployment
will be destroyed (LXC containers will be stopped).

How to develop and/or run a specific functional tests
-----------------------------------------------------

Functional tests are designed to be run from the puppetmaster.
The recommended way to edit/add a new test is to work on it locally and then use this combination of rsync/ssh to actually run the test:

.. code-block:: bash

  $ rsync -av tests/ puppetmaster:puppet-bootstrapper/tests/ && ssh -t puppetmaster nosetests --no-byte-compile -s -v puppet-bootstrapper/tests/functional/

Tips: ::

 * '-s' enables the use of 'import pdb; pdb.set_trace()' within a test
 * '--no-byte-compile' makes sure no .pyc are run
 * you can use file globs to select specific tests: [...]/tests/functional/*zuul*
 * in order to have passwordless ssh and dns configuration, here is a convenient .ssh/config file:

.. code-block:: none

  Host *
    StrictHostKeyChecking no
    User root
  Host puppetmaster
    Hostname 192.168.134.49
  Host mysql
    Hostname 192.168.134.50
  Host redmine
    Hostname 192.168.134.51
  Host gerrit
    Hostname 192.168.134.52
  Host jenkins
    Hostname 192.168.134.53
  Host managesf
    Hostname 192.168.134.54
  Host slave
    Hostname 192.168.134.55


How to contribute
-----------------

* Connect to http://softwarefactory.enovance.com/_r/ using your Github account
* Register your public SSH key on your account. Have a look to: :ref:`Adding public key`.
* Check the bugtracker and the pending reviews
* Submit your change

.. code-block:: bash

  $ cd /srv/software-factory
  $ git-review -s # only relevant the first time to init the git remote
  $ git checkout -b"my-branch"
  $ # Hack the code, create a commit on top of HEAD ! and ...
  $ git review # Summit your proposal on softwarefactory.enovance.com

Have a look to http://softwarefactory.enovance.com/_r/ where you will find the patch
you have just submitted. Automatic tests are run against it and Jenkins/Zuul will
report a status as comments on the Gerrit page related to your patch. You can
also check http://softwarefactory.enovance.com/_zuul/ to follow the test process.

Note that Software Factory is developed using Software Factory. That means that you can
contribute to SF in the same way you would contribute to any other project hosted
on SF: :ref:`contribute`.

Feel free to hack the code, update your test deployment and contribute !
