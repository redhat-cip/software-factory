.. toctree::

Configure automatic tests for a project
=======================================

The big picture
---------------

Software Factory relies on Zuul to enable a CI workflow. If you
want to have a deeper understanding of Zuul then you can have a
look at the `official documentation <http://docs.openstack.org/infra/zuul/>`_ and/or at this
`blog post <http://techs.enovance.com/7542/dive-into-zuul-gated-commit-system-2>`_.

By default a Software Factory deployment embeds a special project
called **config**. The purpose of this project is to store all the
Jenkins and Zuul configurations that details how to run tests for
each projects hosted on Software Factory.

This project is pre-filled by default with default Jenkins Job Builder (JJB)
templates and also a default Zuul layout file.

The default Zuul layout.yaml provides five pipelines:

* The **check** pipeline: Is used to run Jenkins jobs
  related to a Gerrit change (a submitted patch) and to report
  a note (-1, or +1) in the **Verified** label according to attached
  tests result. This pipeline is managed by the independent
  manager of Zuul.

* The **gate** pipeline: Jobs can be configured to run in this pipeline
  after a change has received all the required approvals,
  (1 (+2) approval on the **Core-Review** label, one (+1) approval on
  the **Workflow** label and 1 (+1) on the **Verified** label).
  This pipeline is managed by the dependent manager of Zuul and acts
  as a `Gated Commit system <https://en.wikipedia.org/wiki/Gated_Commit>`_.

* The **post** pipeline: Is used to run Jenkins jobs
  after a change has been merged into the master branch of a
  project. No score is given to the related change regardless of success
  or failure. This pipeline is managed by the independent manager of Zuul.

* The **periodic** pipeline: Is used to run periodic (a bit like a
  cron job) Jenkins jobs. Since these jobs are not related to a change, no
  score is given either.
  This pipeline is managed by the independent manager of Zuul.

* The **tag** pipeline: Jobs are triggered after a tag is pushed on a
  project. Like the post and periodic pipelines, there is no score associated
  to the results of these jobs.

This default pipeline's configuration can be customized according to your
needs.

More informations about Zuul managers can be found
`here <http://docs.openstack.org/infra/zuul/zuul.html#pipelines>`_.

Software Factory eases Jenkins jobs definition by using Jenkins
Job Builder (JJB). Basically JJB is a definition format in yaml
that allow you to easily configure and define Jenkins Jobs.

More information about Jenkins Job Builder can be found
`here <http://docs.openstack.org/infra/jenkins-job-builder/definition.html>`_.

As said before Software Factory stores this configuration in
the special **config** repository. So adding/changing a Jenkins Job
is simply making a change in that **config** repository as
usual, by using **git review**. That change is automatically verified
and, once merged in the master branch of the **config** repository, Zuul
triggers Jenkins Job Builder and a Zuul's "reload conf" to take care of
that new change.

.. graphviz:: test_workflow.dot

Default architecture
--------------------

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

How to define tests for a new project
-------------------------------------

In order to have tests running on a new patch change, you need to:

* Checkout the config repository

.. code-block:: bash

 $ git clone http://{sf-gateway}/r/config

You will find some yaml files related to JJB (Jenkins Job Build) and Zuul. There are two specific
files that you can modify according to your needs:

 - jobs/projects.yaml (JJB)
 - zuul/projects.yaml (Zuul)

The other files may be modified by an upgrade of Software Factory and *shouldn't be modified manually*.

Edit jobs/projects.yaml to define jobs for your project. e.g., to get the project
"sfstack" created with 2 jobs on Jenkins:

.. code-block:: yaml

 - project:
     name: sfstack
     jobs:
       - 'sfstack-unit-tests'
       - 'sfstack-functional-tests'

The definition above use the default job templates provided by jobs/sf_jjb_conf.yaml.

Edit zuul/projects.yaml to configure when jobs get executed, e.g., to get the unit and
functional tests run on check and gate pipelines:

.. code-block:: yaml

 - name: sfstack
   check:
     - sfstack-unit-tests
     - sfstack-functional-tests
   gate:
     - sfstack-unit-tests
     - sfstack-functional-tests

Once your modifications are done, you need to commit and push your change on Gerrit. Please
refer to :ref:`publishchange` if you don't know how to use **git-review** to send a new path
review on Gerrit.

Once your new patch on the *config* repository has been submitted, the change will be automatically
tested by Jenkins in order to check if the syntax is correct and if the your change can be handled
by JJB and Zuul. Then the patch must be peer reviewed, accepted and pushed to master via
the Gerrit UI. Once published to *config* master branch, the tests will be executed by Zuul/Jenkins
for each patch on the *sfstack* project in this example.

Define your own jobs
--------------------

Clone or pull the config repository:

.. code-block:: bash

 $ git clone http://[sf-gateway}/r/config

Edit jobs/projects.yaml to define your new job:

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

Then you need to attach this jobs to project(s) and pipeline(s) as shown in previous chapter by
modifying zuul/projects.yaml.

Some quick explanation about this job configuration:

- defaults: is the way the workspace is prepared. In Software Factory default's configuration
  this defines a freestyle project that can be run concurrently.
- builders: The builder is the job code. It is important to note that it uses the default
  "prepare-workspace" builder and then the "shell" one. The former uses "zuul-cloner" to
  checkout the project + the change to be tested in the workspace. Then the later uses
  ZUUL_PROJECT to jump into the project source directory and then performs your custom actions.
- wrappers for credential bindings (optional): this makes credentials defined in Jenkins available
  in the job's workspace. In this example, a file will be created and stored in the path set by the
  shell variable ${my_secret_file} for the duration of the job.
- triggers: using "zuul" trigger is mandatory to expose environments variables (set by
  zuul's scheduler) in the job workspace. Indeed "zuul-cloner" use them. ZUUL_PROJECT is
  also part of these variables.
- node: is the slave label that specify where the job can be executed.

As explained in the previous chapter you need to submit and have your change merged on
Gerrit *config* repository to have this new test triggered.

Configure a job as "Non Voting"
-------------------------------

A test result for a patch determines if the patch is ready to be merged. Indeed Zuul
reports an evaluation on Gerrit at the end of the test execution and if this result,
is positive, then it allow the patch to be merged on the master branch of a project. But
it can be long and difficult to develop a new test that work correctly (stable, not raises
false-positive, ...) so a good practice is to first setup the job as "Non Voting".

For instance, for a project you have already one test job that is known as stable and
reports a note on Gerrit and by the way conditions the merge of a patch. Then you
want to add another test job but you don't want this new job blocks the merge of
a patch because your are not yet confident with that test. In that case you
can configure Zuul (zuul/projects.yaml) as follow:

.. code-block:: yaml

 jobs:
   - name: demo-job
     branch: master
     voting: false

Zuul will then reports the "demo-job" result as a comment for the tested patch
but wont set the global note negative.

Configure logs/artifacts export
-------------------------------

Export in a Swift server
........................

A default publisher is provided with Software Factory "zuul-swift-upload".
You can attach it to jobs as follow:

.. code-block:: yaml

 - builder:
    name: myapp-fetch-artifacts
    builders:
      - shell: |
          mkdir artifacts
          ./test/myapp-artifacts-copy.sh artifacts/

 - publisher:
    name: myapp-fetch-artifacts
    publishers:
      - postbuildscript:
          builders:
            - myapp-fetch-artifacts
          script-only-if-succeeded: False
          script-only-if-failed: False

 - job:
    name: myapp-test
    defaults: global
    builders:
      - prepare-workspace
      - shell: |
          ./run_functional_tests.sh
    publishers:
      - myapp-fetch-artifacts
      - zuul-swift-upload
    triggers:
      - zuul
    node: bare-centos-7


Note the additional publisher "myapp-fetch-artifacts" that is
a custom script that you may have in your project to retreive all produced
logs/artifacts by a job/test. This custom publisher is executed whatever
the "./run_functional_tests.sh". All logs/artifacts must be copied in the
"artifacts" directory at the root of the workspace.

The second publisher to be executed is the default zuul-swift-upload that will
look for a local "artifacts" directory. This publisher assume that the
Software Factory has been configured to allow the export of logs/artifacts
into a Swift server.

The Jenkins console log is not exported to the swift server and a link
to access the console will be still reported to Gerrit allowing you
to browse the stdout output of your job.

To ease the access of the logs/artifacts from the Jenkins console you
can display the url contained in the environment variable : "SWIFT_artifacts_URL".

Furthermore in order to trigger the creation by Zuul of all needed variables
that allow the export by the publisher zuul-swift-upload in Swift
you have to define a job like as follow in (zuul/projects.yaml):

.. code-block:: yaml

 jobs:
   - name: myapp-test
      swift:
        - name: artifacts

The publisher uses the formpost capability of Swift. The cluster needs to enable
staticweb middleware too.

The Software Factory administrator should have configured Zuul via sfconfig.yaml
to allow you to use that feature.


Custom
......

You can use Jenkins Jobs builder to define/configure a new publisher as long
as the Jenkins' plugin you intend to use is included in Software Factory.

Parallel testing
----------------

Running tests in parallel is somewhat challenging. Let's assume two patches are
verified successfully independently and get merged, but will fail once they are
merged together. zuul-merger avoids this by merging several patches during testing.

.. graphviz:: zuul.dot

Setup a Jenkins slave
---------------------

If you need to setup one or more Jenkins slaves, you can follow the process below:

To substitute:

 - <gateway>: The same name you access the SF Web user interface.
 - <password>: The password of the Jenkins user.

.. code-block:: bash

 $ # Add the jenkins user
 $ sudo adduser --disabled-password --home /var/lib/jenkins jenkins
 $ # You can setup sudo for the jenkins user in order to have the possibility
 $ # to run command via sudo in your tests.
 $ sudo -i
 $ cat << EOF > /etc/sudoers.d/jenkins
   Defaults   !requiretty
   jenkins    ALL = NOPASSWD:ALL
   EOF
 $ chmod 0440 /etc/sudoers.d/jenkins
 $ exit
 $ # Download and start the swarm client
 $ sudo -u jenkins curl -o /var/lib/jenkins/swarm-client-1.22-jar-with-dependencies.jar \
    http://maven.jenkins-ci.org/content/repositories/releases/org/jenkins-ci/plugins/\
    swarm-client/1.22/swarm-client-1.22-jar-with-dependencies.jar
 $ sudo -u jenkins bash
 $ /usr/bin/java -Xmx256m -jar /var/lib/jenkins/swarm-client-1.22-jar-with-dependencies.jar \
   -fsroot /var/lib/jenkins -master http://<gateway>:8080/jenkins -executors 1 -username jenkins -password \
   <password> -name slave1 &> /var/lib/jenkins/swarm.log &


You should check the swarm.log file to verify the slave is well connected to the jenkins master. You can
also check the Jenkins Web UI in order to verify the slave is listed in the slave list.

Then you can customize the slave node according to your needs to install components
required to run your tests.

The Jenkins user password can be fetched from the file sfcrefs.yaml on the
puppetmaster node. You can find it with the following command or request it from
your Software Factory administrator.

If you want this slave authorizes jobs to be run concurrently then modify the "executors"
value.

.. code-block:: bash

 $ grep creds_jenkins_user_password sf-bootstrap-data/hiera/sfcreds.yaml
