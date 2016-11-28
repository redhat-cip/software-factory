.. _sf-arch:

Modular Architecture: arch.yaml
===============================

SF architecture is modular and defined by a single file called arch.yaml. This
file defines the number of nodes, their requirements in term of resources and
how services are distributed. While every services can be dispatched to a
dedicated node, it is advised to use the allinone refarch first, and then do
scale-up as needed (such as moving the SQL database or the ELK stack to
a separate node).


Configuration
-------------

The architecture is defined in /etc/puppet/hiera/sf/arch.yaml:

.. code-block:: yaml

  inventory:
    - name: node01
      roles:
        - install-server
        - mysql

    - name: node02
      mem: 8
      roles:
        - gerrit

.. note::

  Any modification to arch.yaml needs to be manually applied with the sfconfig.sh script.
  Run sfconfig.sh after saving the sfconfig.yaml file.


The minimal architecture includes following components:

* mysql
* gateway
* cauth
* managesf
* gerrit
* zuul
* jenkins

Optional services can be enabled:

* gerritbot
* etherpad
* lodgeit
* nodepool
* redmine
* mirror
* murmur

More services are also available, but their integration is still in progress, e.g.: "tech preview":

* storyboard, storyboard-webclient
* elasticsearch, job-logs-gearman-client, job-logs-gearman-worker, logstash, kibana
* repoxplorer


Extending the architecture
--------------------------

To deploy a specific service on a dedicated instance:

* Start a new instance using the SF image (same version as the main one) on the same network with the desired flavor
* Attach a dedicated volume if needed
* Make sure other instances security group allows network access from the new instance
* Add root public ssh key (install-server:/root/.ssh/id_rsa.pub) to the new instance,
* Make sure remote ssh connection access happen without password authentication,
* Add the new instance to the arch inventory and set it's ip address,
* Add desired services in the roles list (e.g., elasticsearch), and
* Run sfconfig.sh to reconfigure the deployment.

See config/refarch directory for example architectures.


Howto run ELK on a dedicated instance
-------------------------------------

This procedure demonstrates how to run the log indexation services (ELK stack) on a dedicated instance:

* First stop and disable all elk related services (elasticsearch, logstash, log-gearman-client and log-gearman-worker)
* Copy the current data, e.g.: rsync -a /var/lib/elasticsearch/ new_instance_ip:/var/lib/elasticsearch/
* Add the new instances and roles to the /etc/puppet/hiera/sf/arch.yaml file:

.. code-block:: yaml

  inventory:
    - name: elk
      ip: new_instance_ip
      roles:
        - elasticsearch
        - logstash
        - log-gearman-client
        - log-gearman-worker

* Run sfconfig.sh
