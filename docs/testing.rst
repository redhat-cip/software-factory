.. toctree::

Configure automatic tests for a project
=======================================

The big picture
---------------

By default a Software Factory deployment embeds a special project
called **config**. The purpose of this project is to store all the
Jenkins and Zuul configurations that details how to run tests for
each projects hosted on Software Factory.

This project is pre-filled by default with default Jenkins Job Builder (JJB)
templates and also a default Zuul layout file.

The default Zuul layout.yaml provided four test pipelines:

* The check pipeline: The intend of that pipeline is to run
  Jenkins jobs (mainly tests) related to a Gerrit
  change (a submitted patch) and to report a note (-1, or +1) in
  the **Verified** label.

* The post pipeline: This pipeline can be use to run Jenkins jobs
  after a change has been merged into the master branch of a
  project. No note are given to the related change if the job fails
  or pass.

* The gate pipeline: In this pipeline Jenkins job can be configured
  to run after a change has received all the required approvals,
  2 approvals on the **Core-Review** label and an approval on
  the **Workflow** label. This pipeline takes care of rebasing the
  change on the master branch and run the related Jenkins jobs
  (mainly tests) and automatically submits the change on the
  master branch in case of success.

* The periodic pipeline: Is used to run periodic (a bit like a
  cron job) Jenkins jobs.

Software Factory eases Jenkins jobs definition by using Jenkins
Job Builder (JJB). Basically JJB is a definition format in yaml
that allow you to easily configure and define Jenkins Jobs.

As said before Software Factory stores this configuration in
the special **config** repository. So adding/changing a Jenkins Job
is simply making a change in that **config** repository as
usual, by using **git review**. That change is automatically verified
and, once merged in the master branch of the **config** repository, SF
triggers Jenkins and Zuul to take care of that new change.

.. graphviz:: test_workflow.dot

How to configure
----------------

New projects and their associated jobs could be configured in the *config* repository.

There are two way to execute jobs:

 * either through Gerrit with a change, then jobs need this configuration:

  * Use zuul defaults
  * No need to checkout code, zuul-git scm will take care of it

 * either through a periodic/non related to Gerrit, then jobs need this configuration:

  * Use global configuration
  * Use gerrit-git-prep builder to checkout either master or a branch

The default configuration provided by software-factory contain some reusable template and
a complete project configured: the config project itself!

Default architecture
--------------------

The default test architecture is based on standard script at the root of your project that
will take care of the actual testing:

* run_tests.sh              run the unit tests
* run_functional-tests.sh   run the functional tests
* publish_docs.sh           publish documentation after a change is merged

Then these scripts are executed by their associated job:

* '{name}-unit-tests'
* '{name}-functional-tests'
* '{name}-publish-docs'

Obviously, adding these pre-defined scripts to your projects in order to have tests
executed is not mandatory and you can define your own.

How to define tests for a new project
-------------------------------------

In order to have tests running on a new patch change, you need to:

* Checkout the config repository

.. code-block:: bash

 $ git clone http://[sf-gateway}/r/config

You will find some yaml files related to JJB (Jenkins Job Build) and Zuul. There are two specific
files that you can modify according to your needs:

 - jobs/projects.yaml (JJB)
 - zuul/projects.yaml (Zuul)

The other files may be modified by an update of Software Factory and *shouldn't be modified manually*.

Edit jobs/projects.yaml to define your project and the related job,
e.g., to get the project "sfstack" created with 2 jobs on Jenkins:

.. code-block:: yaml

 - project:
     name: sfstack
     jobs:
       - 'sfstack-unit-tests'
       - 'periodic-sfstack-unit-tests'

Edit zuul/projects.yaml to configure when jobs get executed, e.g., to get the unit tests
run on check pipelines and also periodically:

.. code-block:: yaml

 - name: sfstack
   check:
     - sfstack-unit-tests
   periodic:
     - periodic-sfstack-unit-tests

Once your modifications are done, you need to commit and push your change on Gerrit. Please
refer to :ref:`publishchange` if you don't know how to use **git-review** to send a new path
review on Gerrit.

Once your new patch on the *config* repository has been submitted, the change will be automatically
tested by Jenkins in order to check if the syntax is correct and if the your change can be handled
by JJB and Zuul. Then the patch must be peer reviewed, accepted and pushed to master via
the Gerrit UI. Once published to *config* master branch, the tests will be executed by Zuul/Jenkins
for each patch on the *sfstack* project in this example.

How to add a new job
--------------------

As mentioned above you may want to define custom jobs. To do that you need to checkout the config
repository and even, if you already have a local copy, rebase the master branch:

.. code-block:: bash

 $ git clone http://[sf-gateway}/r/config

Edit jobs/projects.yaml to define your new job:

.. code-block:: yaml

 - job:
     name: 'demo-job'
     defaults: zuul
     builders:
       - shell: |
           set -e
           sloccount .
           echo do a custom check/test
     node: slave1.myslavepool.demo.org

Then you need to attach this jobs to a project and zuul pipelines as shown in previous chapter by
modifying jobs/projects.yaml and zuul/projects.yaml.

Some quick explanation about this job configuration:

- defaults: is the way job are executed, it is either "zuul" (for gerrit change) or "global" (e.g., for periodic or post job)
- builders: is the actual job code
- node: is the slave label that will execute the job

As explained in the previous chapter you then need to submit and publish the change on Gerrit
to execute your new job.

Configure a job as "Non Voting"
-------------------------------

A test result for a patch determines if the patch is ready to be merged. Indeed Zuul
reports an evaluation on Gerrit at the end of the test execution and if this result,
is positive, then it allow the patch to be merged on the master branch of a project. But
it can be long and difficult to develop a new test that work correctly (stable, not raises
false-positive, ...) so a good practice is to first setup the test job as "Non Voting".

For instance, for a project you have already one test job that is known as stable and
reports a note on Gerrit and by the way condition the merge of the patch. Then you
want to add another test job but you don't want this new on to block the merge of
patches because your are not yet confident with that test. In that case you
can configure Zuul (zuul/projects.yaml) as follow:

.. code-block:: yaml

 jobs:
   - name: my-new-test
     branch: master
     voting: false

Zuul will then reports the "my-new-test" result as a comment for the tested patch
but wont set the global note negative.

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
   -fsroot /var/lib/jenkins -master http://<gateway>:8080/jenkins -username jenkins -password \
   <password> -name slave1 &> /var/lib/jenkins/swarm.log &


You should check the swarm.log file to verify the slave is well connected to the jenkins master. You can
also check the Jenkins Web UI in order to verify the slave is listed in the slave list.

Then you can customize the slave node according to your needs to install components
required to run your tests.

Note: The Jenkins user password can be fetched from the file sfcrefs.yaml on the
puppetmaster node.

.. code-block:: bash

 $ grep creds_jenkins_user_password puppet-bootstrapper/build/hiera/sfcreds.yaml

Useful commands
---------------

Trigger the periodic pipeline at will
.....................................

.. code-block:: bash

 $ zuul enqueue --trigger timer --pipeline periodic --project all --change 0,0
