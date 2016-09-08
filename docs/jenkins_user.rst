.. _jenkins-user:

Jenkins jobs configuration
==========================

`Jenkins <https://jenkins.io/>`_ is a continuous integration tool.

Jobs are configured in the config-repo jobs/ directory using
`Jenkins Job Builder (JJB) <http://docs.openstack.org/infra/jenkins-job-builder/>`_. Basically JJB is a definition format in yaml that allow you to easily configure and define Jenkins Jobs.


Default tests
-------------

The default test architecture is based on standard scripts at the root of
your project.

* run_tests.sh              run the unit tests
* run_functional-tests.sh   run the functional tests
* publish_docs.sh           publish documentation after a change is merged

Then these scripts are executed by their associated job:

* '{name}-unit-tests'
* '{name}-functional-tests'
* '{name}-publish-docs'

If a project is a python library, the template job '{name}-upload-to-pypi' can
be used to push a package to a PyPI server. A valid .pypirc file set as a
Jenkins credential must exist first; the id of the credential must then be
passed as the variable 'pypirc' when configuring the job for the project.
More information about the .pypirc file format can be found
`here <https://docs.python.org/2/distutils/packageindex.html#pypirc>`_.

Obviously, adding these pre-defined scripts to your projects in order to have tests
executed is not mandatory. You can define your own.


Adding new jobs
---------------

To add new job, create a new file, for example jobs/project.yaml:

.. code-block:: yaml

 - project:
     name: sfstack
     jobs:
       - 'sfstack-unit-tests'
       - 'sfstack-functional-tests'


The above example defines two jobs, 'sfstack-unit-tests' and 'sfstack-functional-tests',
read :ref:`zuul project gating<zuul-gate>` to see how to automatically run
those jobs on new patchs.


Adding custom jobs
------------------

New job can be created without using the provided template:

.. code-block:: yaml

 - job:
     name: 'demo-job'
     defaults: global
     builders:
       - prepare-workspace
       - shell: |
           cd $ZUUL_PROJECT
           set -e
           sloccount .
           echo do a custom check/test
     wrappers:
       - credentials-binding:
         - file:
            credential-id: c6a71f95-be85-4cad-9cec-3bea066ee80a
            variable: my_secret_file
     triggers:
       - zuul
     node: centos7-slave

Some explanation about this job configuration:

* defaults: is the way the workspace is prepared. In Software Factory default's configuration
  this defines a freestyle project that can be run concurrently.
* builders: The builder is the job code. It is important to note that it uses the default
  "prepare-workspace" builder and then the "shell" one. The former uses "zuul-cloner" to
  checkout the project + the change to be tested in the workspace. Then the later uses
  ZUUL_PROJECT to jump into the project source directory and then performs your custom actions.
* wrappers for credential bindings (optional): this makes credentials defined in Jenkins available
  in the job's workspace. In this example, a file will be created and stored in the path set by the
  shell variable ${my_secret_file} for the duration of the job.
* triggers: using "zuul" trigger is mandatory to expose environments variables (set by
  zuul's scheduler) in the job workspace. Indeed "zuul-cloner" use them. ZUUL_PROJECT is
  also part of these variables.
* node: is the slave label that specify where the job can be executed.


