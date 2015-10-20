.. toctree::

Configure slave nodes for Jenkins
=================================

This section describes the method to attach Jenkins slaves to the Jenkins master
we provide in SF.

Automatic setup via the Jenkins UI
----------------------------------

The easiest way is to start a VM and allow the Jenkins master to connect via
SSH on it. Indeed Jenkins is able to convert a minimal VM to a Jenkins slave.
Nevertheless the minimal VM needs some adjustments in order to let Jenkins
start the swarm process.

The instructions below are adapted to Centos 7 but should work on others Linux
distributions.

.. code-block:: bash

 $ sudo yum install -y epel-release
 $ sudo yum install -y java-1.8.0-openjdk python-pip gcc python-devel
 $ sudo pip install zuul
 $ sudo useradd -m jenkins
 $ sudo gpasswd -a jenkins wheel
 $ echo "jenkins ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/jenkins-slave
 $ echo 'Defaults   !requiretty' | sudo tee --append /etc/sudoers.d/jenkins-slave
 $ sudo chmod 0440 /etc/sudoers.d/jenkins-slave
 $ sudo mkdir /home/jenkins/.ssh
 $ sudo chown -R jenkins /home/jenkins/.ssh
 $ sudo chmod 700 /home/jenkins/.ssh
 $ sudo chmod 600 /home/jenkins/.ssh/authorized_keys

Then copy inside "/home/jenkins/.ssh/authorized_keys" the public key of Jenkins that you
can find in this file "/root/sf-bootstrap-data/ssh_keys/jenkins_rsa.pub" on the SF instance.

As the administrator, go in "Manage jenkins"/"Manage nodes"/"New node" and select
"Dumb node" plus add a node name. Keep the amount of executor to 1 if your jobs can't
run in paralllel. Set the "Remote root directory" to "/home/jenkins". Add the needed
label (your are going to use that label in the JJB descriptions of your jobs).
Keep "Launch slave agents on Unix machines via SSH" and the default credential
"jenkins (slave)" then enter the IP address of the VM you just created. Save, then
you should see the Slave appears in the Slave list.

Manual setup of a Jenkins slave
-------------------------------

You can follow the process below to configure manually a Jenkins slave.

You will need to substitute:

 - <sf-hostname>: the one you defined in sfconfig.yaml (domain).
 - <jenkins-password>: The password of the Jenkins user. You can find it in
   "/root/sf-bootstrap-data/hiera/sfcreds.yaml" (creds_jenkins_user_password)

The instructions below are adapted to Centos 7 but should work on others Linux
distributions.

.. code-block:: bash

 $ sudo yum install -y epel-release
 $ sudo yum install -y java-1.8.0-openjdk python-pip gcc python-devel
 $ sudo pip install zuul
 $ sudo useradd -m jenkins
 $ sudo gpasswd -a jenkins wheel
 $ echo "jenkins ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/jenkins-slave
 $ echo 'Defaults   !requiretty' | sudo tee --append /etc/sudoers.d/jenkins-slave
 $ sudo chmod 0440 /etc/sudoers.d/jenkins-slave
 $ # Download and start the swarm client
 $ sudo -u jenkins curl -o /home/jenkins/swarm-client-1.22-jar-with-dependencies.jar \
    http://maven.jenkins-ci.org/content/repositories/releases/org/jenkins-ci/plugins/\
    swarm-client/1.22/swarm-client-1.22-jar-with-dependencies.jar
 $ sudo -u jenkins bash
 $ /usr/bin/java -Xmx256m -jar /home/jenkins/swarm-client-1.22-jar-with-dependencies.jar \
   -fsroot /home/jenkins -master http://<sf-hostname>:8080/jenkins -executors 1 -username jenkins -password \
   <jenkins-password> -name slave1 &> /home/jenkins/swarm.log &


You should check the swarm.log file to verify the slave is well connected to the Jenkins master. You can
also check the Jenkins Web UI in order to verify the slave is well listed in the slave list.

Then you can customize the slave node according to your needs to install components
required to run your tests.

If you want this slave authorizes jobs to be run concurrently then modify the "executors"
value.

Using nodepool to manage Jenkins slaves
---------------------------------------

Nodepool automates management of Jenkins slave. It automatically prepares and
starts VMs that are used for a single job. After each jib the VM is destroyed
and a fresh one is started for the next job. Nodepool also prepares the images
that are used for testing, for example when additional packages are required.

To do this, an account on an OpenStack cloud is required and credentials need to
be known by Nodepool.

In order to configure Nodepool to define a provider (an OpenStack cloud account) you need
to adapt sfconfig.yaml. Below is an example of configuration.

.. code-block:: yaml

 nodepool_os_password: 'secret'
 nodepool_os_project_id: 'tenantname'
 nodepool_os_auth_url: 'http://localhost:35357/v2.0'
 # Compute availability zone
 nodepool_os_pool: 'nova'
 # Max amount of Slaves that can be started
 nodepool_os_pool_max_amount: 10
 # Delay in seconds between two tasks within nodepool
 nodepool_provider_rate: 10.0

To apply the configuration you need to run again the sfconfig.sh script.

You should be able to validate the configuration via the nodepool client by checking if
Nodepool is able to authenticate on the cloud account.

.. code-block:: bash

 $ nodepool list
 $ nodepool image-list

Build scripts, images and labels definition are done via the config repository of SF.

By default SF provides a build script called "base.sh" that is the minimal script to run
by Nodepool in order to prepare a working slave and attach it to Jenkins. Two yaml files
are also provided: labels.yaml and images.yaml.

Nodepool first needs to prepare snapshots of declared images before being able to spawn
Jenkins slaves. The following is the process to define an image for Nodepool.

Clone the config repository of SF from Gerrit and modify the file "config/nodepool/images.yaml"
as below.

.. code-block:: yaml

  - provider: default
    images:
     - name: bare-centos-7
       base-image: CentOS-7-cloud
       username: centos
       private-key: /var/lib/jenkins/.ssh/id_rsa
       setup: base.sh
       min-ram: 2048

Basically here nodepool will start a VM on the provider you defined in sfconfig.yaml using
the Glance image "CentOS-7-cloud". Nodepool will connect on it using the username "centos"
and the SSH key /var/lib/jenkins/.ssh/id_rsa". Then Nodepool will use "base.sh" to configure
the VM. Finally Nodepool will snapshot and destroy the VM.

Note the "CentOS-7-cloud" image must be already available in Glance.

Then define a new label in the file "config/nodepool/labels.yaml"

.. code-block:: yaml

 labels:
   - name: bare-centos-7
     image: bare-centos-7
     min-ready: 1
     providers:
       - name: default

Above we tell Nodepool to spawn at least one slave on the default provider from the
"bare-centos-7" image snapshot. The slave will be identified via the label "bare-centos-7".

By committing those two changes on the config repository, SF will perform a file syntax
validation and will allow you (or not) to merge the change (by CR +2 and W +2). Once merged
the new configuration of nodepool will be loaded by the Nodepool service. And you should
see on the declared provider the following:

 * A VM is spawned (with the term "template" in its name)
 * After the run of the base.sh script, the VM is snapshoted
 * The VM is destroyed and the snapshot is available
 * At least one VM is spawned based on the snapshot
 * A floating ip is attached to the new VM
 * The new VM is attached to Jenkins as slave

Using the config repository, SF users can provide custom build scripts for Jenkins slave
as well as custom labels for their jobs' needs. As already said slaves are destroyed after
each job. This can have some advantages:

 * A clean VM for each job
 * A job have full system access (root)

As an administrator, it can be really useful to check /var/log/nodepool/ to debug the Nodepool
configuration.
