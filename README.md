Software Factory - The ready to use Continuous Integration platform
===================================================================

Software Factory is a collection of exisiting tools that aims to
provide a powerful platform to collaborate on software development.
Software Factory eases the deployment of this platform and adds an
additional layer for management. Software Factory is designed to be
deployed inside LXC containers or on an Openstack compatible cloud.

The platform deployed by Software Factory is based on two main
tools that you may already know, Gerrit and Jenkins. This duo have
proven their robustess in some huge projects, especially Openstack
where hundreds of commits are pushed and automatically tested each
day.

Software Factory will highly facilitate the deployment and
configuration of such tools. Indeed, instead of losing time trying
to understand the deployment details for each component, Software
Factory will bootstrap a working platform for you in minutes.

You can install Software Factory either:

* On a VM where LXC and AUFS are enabled
* On VMs using your account with an Openstack Compatible cloud provider

Components SF provides
----------------------

The Software Factory platform is composed of these main components:

* Gerrit - A code review system
* Jenkins - A continous integration system
* Zuul - A Smart project gating system (http://ci.openstack.org/zuul)
* Redmine - A project management and bug tracking system
* Etherpad - A collaborative real time editor (https://github.com/ether/etherpad-lite)
* Lodgeit - A pastebin

We added glue between the components to improve the user experience:

* SSO - Authenticate only once to use all services (Gerrit, Redmine, Jenkins)
* Common authentication backend - Github OAuth or your LDAP directory
* A REST interface - Unified management of projects, groups, users
* JJB (Jenkins Job Builder) - An easy way to manage your Jenkins jobs

SF in detail
------------

For more details please have a look at our documentation here:

http://softwarefactory.enovance.com/docs/

What it looks like
------------------

To connect to our Software Factory instance, simply click here:

http://softwarefactory.enovance.com

Authenticate with your Github account to login.

Software Factory is developed **and tested** using a public instance
of itself.  This means the GitHub repository is just a mirror, and
there are no Travis CI tests configured to run on it.

Contact us
----------

IRC: #softwarefactory on Freenode
MAIL: softwarefactory@enovance.com
