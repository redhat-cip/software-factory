.. _zuul-user:

Zuul pipelines and gating configuration
=======================================

`Zuul <https://docs.openstack.org/infra/zuul/>`_ is a program that is used to gate the source code repository of a project so that changes are only merged if they pass tests.

Most of its configuration are available to Software Factory user through
the config-repo zuul/ directory. Note that it's possible to split the
configuration according to this `upstream spec <https://specs.openstack.org/openstack-infra/infra-specs/specs/zuul_split.html>`_ that hasn't been implemented
yet.

If you want a deeper understanding of Zuul then check the
`official documentation <http://docs.openstack.org/infra/zuul/>`_ and/or this
`blog post <http://techs.enovance.com/7542/dive-into-zuul-gated-commit-system-2>`_.



Pipelines default configuration
-------------------------------

The default Zuul _layout.yaml provides five pipelines:

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


Adding new pipelines
--------------------

To add a custom pipeline, create a new file, for example zuul/periodic.yaml:

.. code-block:: yaml

    pipelines:
      - name: monthly_periodic
        description: This pipeline run every months
        manager: IndependentPipelineManager
        precedence: low
        trigger:
          timer:
            - time: '0 0 1 * \*'
        failure:
          smtp:
            from: jenkins@fqdn
            to: dev-robot@fqdn
            subject: 'fqdn: Monthly periodic failed'


More informations about Zuul pipelines can be found
`here <http://docs.openstack.org/infra/zuul/zuul.html#pipelines>`_.


.. _zuul-gate:

Project's gate
--------------

To add a zuul gate for a project, create a new file, for example zuul/project.yaml:

.. code-block:: yaml

  projects:
    - name: project-name
      check:
        - check-job1-name
        - check-job2-name
      gate:
        - gate-job1-name
        - gate-job2-name
      periodic:
        - periodic-job-name

.. note::

  * Job needs to be defined in job directory too, see :ref:`Job configuration<jenkins-user>`.
  * Check and gate jobs can be identical (and often are).


.. _non-voting-jobs:

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


Export to an OpenStack Swift server
...................................

See the :ref:`Swiftlogs operator documentation<swiftlogs-operator>` and the
:ref:`user documentation<swiftlogs-user>`.


