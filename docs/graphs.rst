Graphs
======

Components
----------
This is an overview of all nodes (shows as dashed boxes) and services and their
connections to each other. Not shown is the puppetmaster server; each node runs
a puppet agent that connects to the puppetmaster server.

.. graphviz:: components.dot

Test Workflow
--------------
.. graphviz:: test_workflow.dot

SSO Authentication
-------------------
SoftwareFactory uses a Single-Sign-On (SSO) authentication for Gerrit, Jenkins and Redmine.
Currently Github (OAuth) and LDAP are supported authentication providers in the central authentication (cauth)
server. 

.. graphviz:: authentication.dot

Parallel testing
----------------
Running tests in parallel is somewhat challenging. Let's assume two patches are
verified successfully independently and get merged, but will fail once they are
merged together.
zuul-merger avoids this by merging several patches during testing.

.. graphviz:: zuul.dot
