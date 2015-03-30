.. toctree::

Getting project statistics in Software Factory
==============================================

You can monitor how your project is going in terms of reviewing activity. The
folks from OpenStack released an tool suite called reviewstats to do so. The
suite includes the following command-line utilities, that can be used with any
instance of Software Factory:

* openreviews : this will show how many reviews are still pending, and statistics
  about reviews waiting time
* reviewers : this will show the reviewers' involvement on the project

Installing reviewstats
----------------------

.. code-block:: bash

 $ git clone https://github.com/openstack-infra/reviewstats.git
 $ cd reviewstats && python setup.py install
 
Using reviewstats
-----------------

The utilities require a JSON file describing the project for which statistics
will be generated. This is what it looks like for the Software Factory project:

.. code-block:: json

 {
    "name": "softwarefactory",
    "subprojects": [
        "sf-docker-poc",
        "sfstack",
        "software-factory"
    ],
    "core-team": [
        "fabien.boucher@enovance.com",
        "christian.schwede@enovance.com",
        "tristan.cacqueray@enovance.com",
        "george.peristerakis@enovance.com",
        "mhuin"
    ]
  }

* name is the name of the project
* subprojects is a list of gerrit projects to consider for statistics retrieval
* core-team is a list of core developers in the subprojects.

The utilities will then be used like so:

.. code-block:: bash

  $ reviewers -p project.json -u <gerrit_user> -k /path/to/gerrit_user_private_key --server softwarefactory.server.url

With the following sample results, taken from Software Factory:

..code-block:: bash

  Reviews for the last 14 days in softwarefactory
  ** -- softwarefactory-core team member
  +------------------+---------------------------------------+----------------+
  |     Reviewer     | Reviews   -2  -1  +1  +2  +A    +/- % | Disagreements* |
  +------------------+---------------------------------------+----------------+
  |     cschwede     |      22    0   2   0  20  12    90.9% |    0 (  0.0%)  |
  |     morucci      |      15    0   3   0  12   9    80.0% |    0 (  0.0%)  |
  | TristanCacqueray |      13    0   5   0   8   3    61.5% |    0 (  0.0%)  |
  |     mhuin **     |       4    0   0   0   4   1   100.0% |    0 (  0.0%)  |
  |      user1       |       2    0   0   0   2   0   100.0% |    0 (  0.0%)  |
  |    peristeri     |       2    0   0   0   2   2   100.0% |    0 (  0.0%)  |
  +------------------+---------------------------------------+----------------+
  Total reviews: 58 (4.1/day)
  Total reviewers: 6 (avg 0.7 reviews/day)
  Total reviews by core team: 4 (0.3/day)
  Core team size: 5 (avg 0.1 reviews/day)
  New patch sets in the last 14 days: 66 (4.7/day)
  Changes involved in the last 14 days: 19 (1.4/day)
    New changes in the last 14 days: 13 (0.9/day)
    Changes merged in the last 14 days: 13 (0.9/day)
    Changes abandoned in the last 14 days: 1 (0.1/day)
    Changes left in state WIP in the last 14 days: 0 (0.0/day)
    Queue growth in the last 14 days: -1 (-0.1/day)
    Average number of patches per changeset: 3.5


