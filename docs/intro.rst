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

An Openstack or Openstack compatible cloud account is needed
to deploy the Software Factory stack. The bootstrap process
will boot all the VMs needed by the platform. Basically
base images must be provisioned in Glance service before starting
the boostrap process. At the end of that process the Software
Factory is ready to use.

Later in that guide we will use SF as Software Factory.

Which components SF provides
----------------------------

The stack is composed of three main components:

* A code review component : `Gerrit <http://en.wikipedia.org/wiki/Gerrit_%28software%29>`_
* A continious integration system : `Jenkins <http://en.wikipedia.org/wiki/Jenkins_%28software%29>`_
* A Smart project gating system: `Zuul <http://ci.openstack.org/zuul/>`_
* A project management and bug tracking system : `Redmine <http://en.wikipedia.org/wiki/Redmine>`_
* A collaborative real time editor : `Etherpad <http://en.wikipedia.org/wiki/Etherpad>`_
* A `pastebin <http://en.wikipedia.org/wiki/Pastebin>`_ like tool : Lodgeit

Which features SF provides
--------------------------

Ready to use development platform
.................................

Setting up a development environment can really be
time consuming and lead sometime to lot of configuration
troubles. SF provides a way to easily deploy such environment
on a running Openstack cloud. The deployment mainly use Openstack
Heat to deploy cloud resources like virtual machines, block
volumes, network security groups, floating IPs. Internal
configuration of services like Gerrit, Jenkins, and others is done
by Puppet. At the end of the process the SF environment deployment
is ready to be used. The whole process from the images uploading
to the system up and ready can take a couple minutes.

Gerrit
......

Gerrit is the main component of the SF. It provides the Git
server, a code review mechanism, a powerful ACLs system. SF
properly configures Gerrit to integrate it correclty with
the issues tracker (Redmine) and the CI system (Jenkins/Zuul).

Some useful plugins are installed on Gerrit:
 - Reviewer-by-blame:
   Automatically adds code reviewers to submitted changes according
   to git-blame result.
 - Replication:
   Add replication mechanism to synchronize internal Git repositories
   to remote location.
 - Gravatar:
   Because sometime it is quite fun to have its gravatar along its
   commits and messages.
 - Delete-project:
   Let the admin the ability to full removed an useless Gerrit project.
 - Download-commands:
   Ease integration of Gerrit with IDE

Some Gerrit hooks are installed to handle Redmine issues:
 - An issue referenced in a commit message will be automatically
   set as "In progress" in Redmine.
 - An issue referenced by a change will be closed when Gerrit
   merge it.

Gerrit is configured to work with Zuul and Jenkins, that means
project tests can be run when changes are proposed to a project.
Tests results are published on Gerrit on the related change as
a note. That note (+1/-1) can support/block the change for merging

Jenkins
.......

Jenkins is deployed along with SF as the CI component. It is
configured to work with Zuul. Zull will control how Jenkins
perform jobs. The SF deployment configure a first Jenkins VM
as master and one Jenkins VM as slave. Additional Jenkins slaved
can be easily added after.

Redmine
.......

Redmine is the issue tracker of the Software Factory. The Redmine
configuration done by the SF is quite standard. Additionaly
we embed the "Redmine Backlogs" plugins that eases Agile
methodologies to be used with Redmine.

Etherpad and Lodgeit
....................

The Software Factory deploys along with Redmine, Gerrit, Jenkins two
other collaboration tools. The first one Etherpad where team can
live edit text documents. This is really handy for instance to
brainstorm of design documents. The second, lodgeit, is simply a
pastebin like tool that facilitates rapid sharing of code snippets,
error stack traces, ...

Unified project creation
........................

SF integrate of REST service that can be used to create and delete
projects on the Software Factory. Thanks to it you can easily
create a project and its related user groups on Gerrit, Redmine
in a couple a seconds. The project deletion automatically clean
all resourses realated to the project on Redmine and Gerrit.

Top menu
........

In order to ease the usage of all those nice tools, SF provides
an unique portal served by one remotely accessible HTTP server.
That means only one hostname to remember in order to access all
the services. Each tool user interface will be displayed with
a little menu on the top of your Web browser screen. By one
click you can move around all SF services.

Single sign on and Github Openid
................................

As it always a pain to deal with login/logout of each component, the
SF provides an unified authentication through Gerrit and Redmine.
Once your are authenticated on Gerrit are on Redmine as well. A
logout from one service logs you out from other service as well.

Beside the standard user backend we provide with SF that is OpenLDAP, we
purpose the ability to register the SF factory against Github to let
user login to Github to be authenticated on the Software Factory.

The future of the Software Factory
----------------------------------

We want to provide :
 - More ready to use integration between components.
 - Ready and easy to used update for SF deployments.
 - Autoscalling using Heat.
 - Developper, Project leaders, Scrum master useful dashboard.
 - Provide choice over issues tracker at deployment time.
