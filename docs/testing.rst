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
  change (a submited patch) and to report a note (-1, or +1) in
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

As said before Software Factory stores this configaration in
the special **config** repository. So adding/changing a Jenkins Job
is simply making a change in that **config** repository as
usual, by using **git review**. That change is automatically verified
and, once merged in the master branch of the **config** repository, SF
triggers Jenkins and Zuul to take care of that new change.

.. graphviz:: test_workflow.dot

How to configure
----------------

To be filled ...


Parallel testing
----------------
Running tests in parallel is somewhat challenging. Let's assume two patches are
verified successfully independently and get merged, but will fail once they are
merged together.
zuul-merger avoids this by merging several patches during testing.

.. graphviz:: zuul.dot
