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




Extending the architecture
--------------------------

To deploy a specific service on a dedicated instance:

* Add root public ssh key (install-server:/root/.ssh/id_rsa.pub) to the new instance,
* Make sure remote ssh connection access happen without password authentication,
* Add the new instance to the arch inventory and set it's ip address,
* Add desired services in the roles list (e.g., elasticsearch), and
* Run sfconfig.sh to reconfigure the deployment.

See config/refarch directory for example architectures.
