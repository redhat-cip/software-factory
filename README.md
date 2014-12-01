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

Software Factory will highly facilitate the deployment and
configuration of a such tools. Indeed instead of losing time to
try to understand deployment details of each components,
Software Factory will bootstrap for you a working platform
within a couple of minutes.

An Openstack or Openstack compatible cloud account is needed
to deploy the Software Factory stack. The bootstrap process
will boot all the VMs needed by the platform, setup network,
and volumes.

It is also possible to run a test deployment in LXC containers.

Which components SF provides
----------------------------

The SF platform is composed of these main components:

* Gerrit - A code review system : http://en.wikipedia.org/wiki/Gerrit_%28software%29
* Jenkins - A continous integration system : Jenkins http://en.wikipedia.org/wiki/Jenkins_%28software%29
* Zuul - A Smart project gating system : http://ci.openstack.org/zuul
* Redmine - A project management and bug tracking system : http://en.wikipedia.org/wiki/Redmine
* Etherpad - A collaborative real time editor : http://en.wikipedia.org/wiki/Etherpad
* Lodgeit - A pastebin like : http://en.wikipedia.org/wiki/Pastebin

We added a glue between those components to improve user experience:

* SSO - Authenticate only once to use all services (Gerrit, Redmine, Jenkins).
* Common authentication backend - LDAP or Github OAuth.
* A REST interface - Unified management of projects, groups, users.
* JJB (Jenkins Job Builder) - Easy way to manage your Jenkins jobs.

SF in details
-------------

For more details please have a look to the SF documentation here: http://softwarefactory.enovance.com/docs/

What it looks like
------------------

We use a public Software Factory instance to develop and test Software Factory. The
Github repository is just a replica. We haven't any tests configured in Travis as
we test Software Factory using Software Factory.

To connect on our Software Factory instance, simply click here :
http://softwarefactory.enovance.com/_r/ and use your Github credentials
to connect.

Contact us
----------

IRC: #softwarefactory on Freenode
MAIL: softwarefactory@enovance.com
