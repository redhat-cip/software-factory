.. toctree::

Deploy Software Factory
=======================

SF is image based, each release is a new archive that includes
a complete operating system and all services pre-installed.

While SF really benefits from running on top of OpenStack, the image
can also be used standalone.

Download the latest image from: https://github.com/redhat-cip/software-factory


Requirements
------------

SF deployment needs:

* Access to an OpenStack Cloud tenant or a standalone CentOS 7
* Minimum 40GB of hardrive and 4GB of memory
* Recommended 80GB of hardrive and 8GB of memory
* FQDN required for web interface OAuth authentication callback

SF can also manage tests running slave instances and test artifact, nodepool and zuul publisher will need:

* One or more dedicated OpenStack tenant to run instance
* A swift endpoint to store and publish tests artifacts

Note that SF will use "tests.dom" as default FQDN and if the FQDN doesn't resolve it needs to be locally
set in etc hosts file because the web interface authentication mechanism redirects browser to the FQDN.

Always make sure to use the last available tag, the example below use the 2.0.0 version. Release
digest are signed with gpg, install the key and verify content with:

.. code-block:: bash

 $ gpg --keyserver keys.gnupg.net --recv-key 0xE46E04A2344803E5A808BDD7E8C203A71C3BAE4B
 $ gpg --verify softwarefactory-C7.0-2.0.0.digest && sha256sum -c softwarefactory-C7.0-2.0.0.digest


OpenStack based deployment
--------------------------

Install image
.............

SF image needs to be uploaded to Glance:

.. code-block:: bash

 $ wget http://os.enocloud.com:8080/v1/AUTH_70aab03f69b549cead3cb5f463174a51/edeploy-roles/softwarefactory-C7.0-2.0.0.img.qcow2
 $ glance image-create --disk-format qcow2 --container-format bare --name sf-2.0.0 --file softwarefactory-C7.0-2.0.0.img.qcow2

Deploy with Heat
................

A Heat template is available to automate the deployment process. It requires the SF image uuid and external Neutron network uuid as
well as the FQDN of the deployment (domain parameter):

.. code-block:: bash

 $ wget http://os.enocloud.com:8080/v1/AUTH_70aab03f69b549cead3cb5f463174a51/edeploy-roles/softwarefactory-C7.0-2.0.0.hot
 $ heat stack-create ./softwarefactory-C7.0-2.0.0.hot -P key_name=SSH_KEY;domain=fqdn_of_deployment;image_id=GLANCE_UUID;sf_root_size=80;ext_net_uuid=NETWORK_UUID


Deploy with Nova
................

When Heat is not available, SF can also be deployed manually using the following process:

* Start the instance and open an admin (root) shell with ssh.
* Edit the configuration sfconfig.yaml (Set the domain and admin username/password).
* Run configuration script.

.. code-block:: bash

 $ nova boot --flavor m1.large --image sf-2.0.0 sf-2.0.0 --key-name SSH_KEY
 $ ssh -A root@sf_instance
 [root@managesf ~]# vim /etc/puppet/hiera/sf/sfconfig.yaml
 [root@managesf ~]# sfconfig.sh


Standalone deployment
---------------------

SF can also be deployed standalone with libvirtd-lxc.

.. code-block:: bash

 $ git clone https://softwarefactory-project.io/r/software-factory
 $ cd software-factory
 $ git checkout 2.0.0
 $ ./sfstack.sh

This method of deployment is mostly useful for testing, it uses default configuration with "tests.dom" domain name and
"user1/userpass" admin username/password.


Multi-node deployment
---------------------

Multi-node deployment is still a work in progress. However all services are configured in virtual domains and are designed
to run independently. Integration tests are currently testing two types of deployments (called reference architectures):

* 1node-allinone: all services run on the same instance.
* 2nodes-jenkins: CI components (jenkins/zuul/nodepool) run on another instance.


Deployment reconfiguration
--------------------------

To change settings like the FQDN, enable github replication, authentication backend or cloud provider...
You need to edit sfconfig.yaml: */etc/puppet/hiera/sf/sfconfig.yaml*.
The configuration script (*sfconfig.sh*) needs to executed again after:

.. code-block:: bash

 [root@managesf ~]# vim /etc/puppet/hiera/sf/sfconfig.yaml
 [root@managesf ~]# sfconfig.sh

If you intend to reconfigure the domain on an already deployed SF, please use the *-d* option of *bootstraps.sh* script.

Network Access
--------------

All network access goes through the main instance (called managesf). The FQDN
used during deployment needs to resolved to the instance floating ip. SF network
access goes through TCP ports:

* 22 for ssh access to reconfigure and update deployment
* 80/443 for web interface, all services are proxyfied on the managesf instance
* 29418 for gerrit access to submit code review
* 8080/45452 for Jenkins swarm slave connection

Note that Heat deployment and Standalone deployment automatically configure
security group rules to allow these connections to managesf.


SF is now ready to be used, dashboard is available at https://FQDN and admin user can authenticate using "Internal Login".
