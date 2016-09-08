.. _nodepool-operator:

Configure nodepool to manage ephemeral test slaves
--------------------------------------------------

Nodepool automates management of Jenkins slave. It automatically prepares and
starts VMs that are used for a single job. After each job the VM is destroyed
and a fresh one is started for the next job. Nodepool also prepares the images
that are used for testing, for example when additional packages are required.


Add a cloud provider
^^^^^^^^^^^^^^^^^^^^

To do this, an account on an OpenStack cloud is required and credentials need to
be known by Nodepool. Moreover it is highly recommended to use a dedicated
network or tenant for slave instances.

In order to configure Nodepool to define a provider (an OpenStack cloud account) you need
to adapt sfconfig.yaml. Below is an example of configuration.

.. code-block:: yaml

 nodepool:
   disabled: false
   providers:
     - auth-url: http://localhost:5000/v2.0
       boot-timeout: 120
       # Max amount of Slaves that can be started
       max-servers: 10
       name: default
       password: 'secret'
       # Compute availability zone
       pool: nova
       project-id: 'tenantname'
       # Dedicated instance network
       network: 'neutron-network-uuid'
       # Delay in seconds between two tasks within nodepool
       rate: 10.0
       username: 'user'

To apply the configuration you need to run again the sfconfig.sh script.

You should be able to validate the configuration via the nodepool client by checking if
Nodepool is able to authenticate on the cloud account.

.. code-block:: bash

 $ nodepool list
 $ nodepool image-list

See the :ref:`Nodepool user documentation<nodepool-user>`

As an administrator, it can be really useful to check /var/log/nodepool/ to debug the Nodepool
configuration.


What to do if nodepool is not working ?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Until this is provided as an automatic task, here is the manual process:

* Check OpenStack provider tenants and clean left-over resources:

  * server with an uptime more than 12 hours
  * glance images
  * unused floating ip

* Remove un-assigned floating-ip
* Check nodepool logs for permission errors or api failure
* Try to update image manually using:
  nodepool image-update <provider_name> <image_name>

If nothing works, this is how to reset the service:

* Stop nodepoold process
* Delete all OpenStack nodepool resources
* Connect to mysql and delete from node, snapshot_image tables
* Manually update image using:
  nodepool image-update <provider_name> <image_name>
* Start nodepoold process
* Follow the logs and wait for servers to be created.
* Check zuul log to verify it is submitting job request.

It might happen that some nodes are kept in the "delete" state for quite some
time, while they are already deleted. This blocks spawning of new instances.
The simplest way to fix this is to clean the stale entries in the nodepool DB
using the following command (deleting all entries older than 24 hours and in
state delete):

.. code-block:: mysql

     DELETE FROM node WHERE state_time < (UNIX_TIMESTAMP() - 86400) AND state = 4;
