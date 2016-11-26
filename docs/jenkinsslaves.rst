Configure slave nodes for Jenkins
=================================

This section describes the method to attach Jenkins slaves to the Jenkins master
provided by SF.


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
 $ sudo touch /home/jenkins/.ssh/authorized_keys
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

When Jenkins slaves are not reachable from the Jenkins master, you can use the swarm client
to do a reverse connection. The following process describe how to manually configure a
Jenkins slave.

You will need to substitute:

 - <fqdn>: the one you defined in sfconfig.yaml (domain).
 - <jenkins-password>: The password of the Jenkins user. You can find it in
   "/etc/software-factory/sfcreds.yaml" (creds_jenkins_user_password)

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
 $ sudo -u jenkins curl -o /home/jenkins/swarm-client-2.1-jar-with-dependencies.jar \
    http://maven.jenkins-ci.org/content/repositories/releases/org/jenkins-ci/plugins/\
    swarm-client/2.1/swarm-client-2.1-jar-with-dependencies.jar
 $ sudo -u jenkins bash
 $ /usr/bin/java -Xmx256m -jar /home/jenkins/swarm-client-2.1-jar-with-dependencies.jar \
   -fsroot /home/jenkins -master http://<fqdn>:8080/jenkins -executors 1 -username jenkins -password \
   <jenkins-password> -name slave1 &> /home/jenkins/swarm.log &


You should check the swarm.log file to verify the slave is well connected to the Jenkins master. You can
also check the Jenkins Web UI in order to verify the slave is well listed in the slave list.

Then you can customize the slave node according to your needs to install components
required to run your tests.

If you want this slave authorizes jobs to be run concurrently then modify the "executors"
value.


Using nodepool to manage Jenkins slaves
---------------------------------------

See the :ref:`Nodepool operator documentation<nodepool-operator>` as well as the :ref:`Nodepool user documentation<nodepool-user>`
