==================================================
Software-Factory project Contributor documentation
==================================================


How can I help?
---------------

Thanks for asking.

The easiest way to get involved is to join us on IRC: #softwarefactory channel on Freenode.

The mailing list is: softwarefactory-dev@redhat.com , subscribe here: https://www.redhat.com/mailman/listinfo/softwarefactory-dev

User stories and bug tracker is available here: http://softwarefactory-project.io/redmine/projects/software-factory/issues


Prepare a development environment
---------------------------------

To get a development environment and a Software Factory up and running,
you need access to a CentOS 7 and execute:

.. code-block:: bash

 sudo yum install -y epel-release
 sudo yum install -y libvirt libvirt-daemon-lxc git git-review vim-enhanced tmux curl python-devel wget python-pip mariadb-devel python-virtualenv python-devel gcc libffi-devel openldap-devel openssl-devel python-sphinx python-tox python-flake8 ansible
 sudo systemctl enable libvirtd
 sudo systemctl start libvirtd
 git clone http://softwarefactory-project.io/r/software-factory
 cd software-factory
 ./fetch_image.sh

There is an included Vagrantfile in the tools directory to automate these tasks
and deploy a usable CentOS 7 instance that can be used for testing:

.. code-block:: bash

 VAGRANT_CWD=./tools/ vagrant up


Optional: use a local http cache
--------------------------------

If you're rebuilding images frequently, it might make sense to cache some
dependency downloads locally. The easiest way to do this is to use a local Squid
instance.

.. code-block:: bash

 sudo yum install -y squid
 sudo sed -ie 's/^http_port.*/http_port 127.0.0.1:3128/g' /etc/squid/squid.conf
 echo "maximum_object_size 100 MB" | sudo tee --append /etc/squid/squid.conf
 echo "cache_dir ufs /var/spool/squid 2000 16 256" | sudo tee --append /etc/squid/squid.conf
 sudo systemctl enable squid
 sudo systemctl start squid

Before you rebuild an image or run functional tests the next time, set the
following environment variables to use the cache. Once dependencies are cached,
it should significantly speed up image building.

.. code-block:: bash

 export http_proxy=http://127.0.0.1:3128
 export https_proxy=http://127.0.0.1:3128


How to run the tests locally
----------------------------

There are five kinds of tests one can run from the development environment (host
hypervisor):

* Unit tests
* Functional tests
* Upgrade tests
* Backup tests
* GUI tests

Before sending a patch to the upstream softwarefactory code, it's better
to run functional and unit tests locally first:

.. code-block:: bash

  ./run_tests.sh                      # unittests
  ./run_functional-tests.sh           # functional tests
  ./run_functional-tests.sh upgrade   # upgrade tests


The functional tests will start LXC container(s) on the local VM to simulate
as close as possible a real deployment:

.. code-block:: bash

  ./run_functional-tests.sh    # run functional tests
  ssh -l root sftests.com      # /etc/hosts entry is automatically added


How to develop and/or run a specific functional tests
-----------------------------------------------------

Functional tests needs access to the keys and configuration of the deployment.
First you need to copy the sf-bootstrap-data/ from the managesf node.

.. code-block:: bash

  rsync -a root@sftests.com:/var/lib/software-factory/bootstrap-data/ sf-bootstrap-data/
  nosetests --no-byte-compile -s -v tests/functional

Tips: ::

 * '-s' enables the use of 'import pdb; pdb.set_trace()' within a test
 * Within a test insert 'from nose.tools import set_trace; set_trace()' to add breakpoint in nosetests
 * '--no-byte-compile' makes sure no .pyc are run
 * you can use file globs to select specific tests: [...]/tests/functional/*zuul*
 * in order to have passwordless ssh and dns configuration, here is a convenient .ssh/config file:

.. code-block:: none

  Host sftests.com
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

  cd /srv/software-factory
  git-review -s # only relevant the first time to init the git remote
  git checkout -b"my-branch"
  # Hack the code, create a commit on top of HEAD ! and ...
  git review # Summit your proposal on softwarefactory-project.io

Have a look to http://softwarefactory-project.io/r/ where you will find the patch
you have just submitted. Automatic tests are run against it and Jenkins/Zuul will
report a status as comments on the Gerrit page related to your patch. You can
also check http://softwarefactory-project.io/zuul/ to follow the test process.

Note that Software Factory is developed using Software Factory. That means that you can
contribute to SF in the same way you would contribute to any other project hosted
on SF: :ref:`contribute`.
