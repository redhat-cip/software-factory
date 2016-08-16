.. _swiftlogs-user:

Export logs to an OpenStack Swift server
========================================

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
to allow you to use that feature. See the
:ref:`Swiftlogs operator documentation<swiftlogs-operator>`


