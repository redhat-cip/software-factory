Contents:

.. toctree::

Introduction to Software Factory
================================

Software Factory is a collection of exisiting tools that aims to
provide a powerful platform to collaborate on software developpemnt.
Software Factory eases the deployment of this platform and add an
additional layer for the managements. Deployment is able on Openstack
compatible cloud.

What is Software Factory
------------------------

The platform deployed by Software Factory is based on two main
tools that you may already know Gerrit and Jenkins. This couple
has proven its robustess in some huge projects and especially
Openstack were hundrends of commit are pushed and automatically
tested in a day.

Software Factory will hightly facilite the deployment and
configuration of a such tools. Indeed instead of losing time to
try to understand deployment details of each components,
Software Factory will bootstrap for you a working platform
within a couple of minutes.

An Openstack or Openstack comptible cloud account is needed
to deploy the Software Factory stack. The bootstrap process
will boot all the VMs needed by the platform. Basically
base images must be provisionned in Glance before starting
the boostrap process. At the end of that process the Software
Factory is ready to use.

Which components we provide
---------------------------

The stack is composed of three main components:

* A code review component : Gerrit
* A continious integration system : Jenkins
* A project management and bug tracking system : Redmine
* A collaborative real time editor : Etherpad
* A pastebin like tool : Lodgeit

The future of the Software Factory
----------------------------------
