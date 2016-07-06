.. toctree::

Deploy Software Factory
=======================

SF is image based, each release is a new archive that includes
a complete operating system and all services pre-installed.

While SF really benefits from running on top of OpenStack, the image
can also be used standalone.

Find the link to the latest image from: https://github.com/redhat-cip/software-factory


Requirements
------------

SF deployment needs:

* **Minimum** 40GB of hardrive and 4GB of memory
* **Recommended** 80GB of hardrive and 8GB of memory
* A name entry (in a DNS or local resolver) for the FQDN of your SF deployment. SF can only be accessed by its FQDN (Authentication will fail if accessed via its IP)

If you intend to manage your jobs/tests on slaves via Nodepool or publish artifacts on Swift you'll need:

* One or more dedicated OpenStack tenant to run instance
* A Swift endpoint to store and publish jobs/tests artifacts

Note that SF will use "sftests.com" as default FQDN and if the FQDN doesn't resolve it needs to be locally
set in */etc/hosts* file because the web interface authentication mechanism redirects browser to the FQDN.

Always make sure to use the last available tag, the example below use the 2.0.0 version. Release
digest are signed with gpg, install the key and verify content with:

.. code-block:: bash

 $ gpg --keyserver keys.gnupg.net --recv-key 0xE46E04A2344803E5A808BDD7E8C203A71C3BAE4B
 $ gpg --verify softwarefactory-C7.0-2.2.2.digest && sha256sum -c softwarefactory-C7.0-2.2.2.digest


Architecture
------------

SF architecture is modular and defined by a single file called refarch::

.. code-block:: yaml

  inventory:
    - name: node01
      roles:
        - install-server
        - mysql
    - name: node02
      roles:
        - gerrit
      mem: 8

Heat and Lxc based deployment autoconfigure dns. Manual deployments needs to edits the
/etc/puppet/hiera/sf/hosts.yaml to set hostname and ip address of other node.

See config/refarch directory for example architectures.


OpenStack based deployment
--------------------------

An account on an OpenStack cloud provider is needed.

Install image
.............

SF image needs to be uploaded to Glance:

.. code-block:: bash

 $ wget http://46.231.132.68:8080/v1/AUTH_b50e80d3969f441a8b7b1fe831003e0a/sf-images/softwarefactory-C7.0-2.2.2.img.qcow2
 $ glance image-create --progress --disk-format qcow2 --container-format bare --name sf-2.2.2 --file softwarefactory-C7.0-2.2.2.img.qcow2

Deploy with Heat
................

Heat templates are available to automate the deployment process of different reference architecture.

They all requires:

* the SF image UUID
* the external Neutron network UUID (using "neutron net-list")
* the FQDN of the deployment (domain parameter)
* a key-pair name (you should have already created it on your account)

.. code-block:: bash

 $ wget http://46.231.132.68:8080/v1/AUTH_b50e80d3969f441a8b7b1fe831003e0a/sf-images/softwarefactory-C7.0-2.2.2-allinone.hot
 $ heat stack-create --template-file ./softwarefactory-C7.0-2.2.2-allinone.hot -P "key_name=SSH_KEY;domain=fqdn_of_deployment;image_id=GLANCE_UUID;ext_net_uuid=NETWORK_UUID;flavor=m1.large" sf_stack

Once the stack is created jump to the section `Configuration and reconfiguration`.

Deploy with Nova
................

When Heat is not available, SF can also be deployed manually using the Nova CLI, or
using the web UI of your cloud provider.

Once the VM is created jump to the section `Configuration and reconfiguration`.
Don't forget to manage by yourself the security groups for the SF deployment `Network Access`.

Outside Openstack
-----------------

Deploy on a local hypervisor
............................

SF can be deployed on a hypervisor without a metadata server accessible (needed by cloud-init).
This is often the case when you are using QEMU, KVM or even VirtualBox. You can boot
a new VM using the SF image and then login via the console using root user.


Then jump to `Configuration and reconfiguration`.

Deployment inside a LXC container
.................................

You need a CentOS 7 VM or physical machine. The libvirtd-lxc package is needed.

.. code-block:: bash

 $ git clone https://softwarefactory-project.io/r/software-factory
 $ cd software-factory
 $ git checkout 2.2.2
 $ ./sfstack.sh

This method of deployment is mostly useful for testing, it uses the default configuration
with "sftests.com" as the FQDN and "admin/userpass" as admin credentials.


Using Virtualbox for testing SoftwareFactory
............................................

You can also use Virtualbox if you want to try out Software Factory on your
desktop.  First, you need to download one of our release images, for example
2.2.2::

 curl -O http://46.231.132.68:8080/v1/AUTH_b50e80d3969f441a8b7b1fe831003e0a/sf-images/softwarefactory-C7.0-2.2.2.img.qcow2

Next, increase the image size to ensure there is enough space is git and the
database and convert the image to make it usable with Virtualbox::

 qemu-img resize softwarefactory-C7.0-2.2.2.img.qcow2 +20G
 qemu-img convert -O vdi softwarefactory-C7.0-2.2.2.img.qcow2 softwarefactory-C7.0-2.2.2.vdi

Now you need to create a new VM in Virtualbox, and use the created .vdi file as
disk. Assign enough memory to it (2GB is a good starting point), and boot the
VM.  Ensure you have at least one network interface besides the loopback
interface up; run ``dhclient`` for example.

Now you need to deploy SF. Run ``sfconfig.sh`` and wait a few minutes while the
system is prepared for you.

Finally, change the root password to make sure you can login afterwards.

Done! The webinterface is enabled on port 80, and the Gerrit git server on port
29418.


Multi-node deployment without LXC or HEAT
-----------------------------------------

When system are deployed manually, you need to reference IP address of all instances.

* Edit /etc/puppet/hiera/sf/arch.yaml to distribute services accross multiple system
* Edit /etc/puppet/hiera/sf/hosts.yaml to set ip address of remote hosts

Note that once the deployment is complete, change to those files is not supported.
To modify the architecure, it needs to be redeployed on new instances and the data needs
to be manually migrated from the previous architecture to the new one.

Configuration and reconfiguration
---------------------------------

First time: **Please read `Root password consideration`**.

* Connect as (root) via SSH.
* Edit the configuration sfconfig.yaml and set the configuration according to your needs.
* Run configuration script.

.. code-block:: bash

 $ ssh -A root@sf_instance
 [root@managesf ~]# vim /etc/puppet/hiera/sf/sfconfig.yaml
 [root@managesf ~]# sfconfig.sh

Notice that the configuration is versioned and it is recommended to use git diff and git commit
command to check files modifications.


Network Access
--------------

All network access goes through the main instance (called managesf). The FQDN
used during deployment needs to resolved to the instance IP. SF network
access goes through TCP ports:

* 22 for ssh access to reconfigure and update deployment
* 80/443 for web interface, all services are proxyfied on the managesf instance
* 29418 for gerrit access to submit code review
* 8080/45452 for Jenkins swarm slave connection

Note that Heat deployment and LXC deployment automatically configure
security group rules to allow these connections to managesf.


SSL Certificates
----------------

By default, SF creates a self-signed certificate. To use another certificate,
such as letsencrypt, you need to update the configuration:

.. code-block:: bash

  hieraedit.py --yaml /etc/puppet/hiera/sf/sfcreds.yaml -f cert.pem    gateway_crt
  hieraedit.py --yaml /etc/puppet/hiera/sf/sfcreds.yaml -f privkey.pem gateway_key
  hieraedit.py --yaml /etc/puppet/hiera/sf/sfcreds.yaml -f chain.pem   gateway_chain
  # apply configuration change
  sfconfig.sh


Access Software Factory
-----------------------

The Dashboard is available at https://FQDN and admin user can authenticate
using "Internal Login". If you used the default domain *sftests.com* then
SF allows (user1, user2, user3) with the default "userpass" password to connect.

If you need more information about authentication mechanisms on SF please refer to
`Software Factory Authentication`.

Root password consideration
---------------------------

Software Factory image comes with an empty root password. root login is only
allowed via the console (**root login with password is not allowed via SSH**). The
empty root password is a facility for folks booting the SF image via a local
hypervisor (without a metadata server for cloud-init).

It is therefore **highly** recommended to deactivate root login via the console
**even booted on OpenStack**.

In order to do that:

.. code-block:: bash

  # echo "" > /etc/securetty

However setting a strong password is one of your possibility.

In environments such as OpenStack a metadata server is accessible and the user public
key will be installed for root and centos users. So user can access the SF node
via SSH using its private SSH key.

**Outside Openstack, when using a local hypervisor** at first root login via the
console the user need to add its public ssh key in */root/.ssh/authorized_key* in
order to be able to access SF node via SSH.
