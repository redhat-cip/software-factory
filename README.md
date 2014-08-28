Software-factory
================

Software Factory is a collection of exisiting tools that aims to
provide a powerful platform to collaborate on software developemnt.
Software Factory eases the deployment of this platform and add an
additional layer for the managements. Software Factory is
designed to be deployed on an Openstack compatible cloud.

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

An Openstack or Openstack compatible cloud account is needed
to deploy the Software Factory stack. The bootstrap process
will boot all the VMs needed by the platform, setup network,
and volumes.

It is also possible to run a test deployement in LXC
containers.

Which components SF provides
----------------------------

The SF platform is composed of these main components:

* Gerrit - A code review system : http://en.wikipedia.org/wiki/Gerrit_%28software%29
* Jenkins - A continious integration system : Jenkins <http://en.wikipedia.org/wiki/Jenkins_%28software%29
* Zuul - A Smart project gating system : http://ci.openstack.org/zuul
* Redmine - A project management and bug tracking system : http://en.wikipedia.org/wiki/Redmine
* Etherpad - A collaborative real time editor : http://en.wikipedia.org/wiki/Etherpad
* Lodgeit - A pastebin like : http://en.wikipedia.org/wiki/Pastebin

SF in details
-------------

For more details please have a look to the SF documentation here:
http://***REMOVED***/v1/***REMOVED***/sfdocs/index.html
