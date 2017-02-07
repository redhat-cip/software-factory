Using Software factory for project development
==============================================

To create a project see :ref:`resources-user`


Contribute to a project on SF
-----------------------------

.. _contribute:

Clone a project
...............

Softwarefactory uses `the GIT protocol <http://en.wikipedia.org/wiki/Git_%28software%29>`_
as its revision control system. When a project is created, Gerrit
initializes the projects' repository.

Repositories can be `cloned <http://git-scm.com/docs/git-clone>`_ from
the Gerrit server to a local directory. Gerrit allows multiple ways to clone
a project repository.

Using HTTP:

.. code-block:: bash

 $ git clone http://{fqdn}/r/{project-name}

Using SSH:

Before accessing the SSH URI, one needs to register the SSH public key of
its user. (See :ref:`setup_ssh_keys`)

.. code-block:: bash

 $ git clone ssh://{user-name}@{fqdn}/{project-name}


Initialize the GIT remote with git-review
.........................................

git-review is a git add-on that manages the reviewing and other aspects of Gerrit.
The way you commit using Gerrit is different compared to using a traditional GIT
repository.

First install git-review. Generally, the easiest way to get last version is
to install it using the Python package installer pip.

.. code-block:: bash

 $ sudo pip install git-review

Then initialize the GIT remote for the project you have cloned. You should
use the SSH way to clone. Please start 'git review -s' as following, the command
will prompt you to enter your Gerrit user name.

.. code-block:: bash

 $ cd <project-name>
 $ git review -s
 Could not connect to gerrit.
 Enter your gerrit username: {user-name}
 Trying again with ssh://{user-name}@{fqdn}:29418/p1
 Creating a git remote called "gerrit" that maps to:
         ssh://{user-name}@{fqdn}:29418/p1


Submit a patch
--------------

Before starting to work it is a good practice to setup a branch and work on it.
The branch name will be displayed as the topic for the patch(es) you are going
to create from it, so give it a meaningful name like bug/{bug-id},
title-bug-fix, ...

To create a branch:

.. code-block:: bash

 $ git checkout -b branch-name
 # Switched to a new branch 'branch-name'
 $ git branch
 * branch-name
   master


Make and commit your change
...........................

Modify your local code in some fashion. At any time, you can see the changes
you made by

.. code-block:: bash

 $ git status
 # On branch branch-name
 # Changes not staged for commit:
 #   (use "git add <file>..." to update what will be committed)
 #   (use "git checkout -- <file>..." to discard changes in working directory)
 #
 #     modified:   modified-file
 #
 # Untracked files:
 #   (use "git add <file>..." to include in what will be committed)
 #
 #     new-file
 no changes added to commit (use "git add" and/or "git commit -a")

You can review the changes you made so far by

.. code-block:: bash

 $ git diff

When you finalize your changes, you need to add the changes by executing

.. code-block:: bash

 $ git add list/of/files/to/add

After adding the files, you need to commit the changes in your local repo

.. code-block:: bash

 $ git commit -m "Detailed description about the change"


Commit message hooks
''''''''''''''''''''

If you are working on a feature or a bug that is defined in a ticket on Redmine,
you can add a line like "Bug: XXX" in your commit message, where XXX is the
ticket number on Redmine. This way, when you submit your change for review, the
ticket will see its status updated to "In Progress"; when the change is merged
the ticket will be closed automatically.
The following keywords are supported:

* bug/Bug
* issue/Issue
* fix/Fix
* close/Close
* Related to/Related-To (this will not close the bug upon merging the patch)

.. _publishchange:


Publishing the change
.....................

Before your changes can be merged into master, they must undergo review in Gerrit.

But first, it's a good idea, but not mandatory, to synchronize your change set
with any changes that may have occurred in master while you've been working.
From within the branch you've been working on, execute the following command:

.. code-block:: bash

 $ git pull --rebase origin master

This command will fetch new commits from the remote master branch and then
rebase your local commit on top of them. It will temporarily set aside the
changes you've made in your branch, apply all of the changes that have happened
in master to your working branch, then merge (recommit) all of the changes you've made
back into the branch. Doing this will help avoid future merge conflicts. Plus, it gives
you an opportunity to test your changes against the latest code in master.

Once you are satisfied with your change set,
you are ready to push your code to Gerrit for code review.

Make sure you had setup git-review before submitting the code for review.

To push the change to Gerrit, execute the following command:

.. code-block:: bash

 $ git review
 # remote: Processing changes: new: 1, refs: 1, done
 # remote:
 # remote: New Changes:
 # remote:   http://{fqdn}/{change-number}
 # remote:
 # To ssh://{user-name}@{fqdn}:29418/{project-name}
 #  * [new branch]      HEAD -> refs/publish/master/branch-name


Amending a change
.................

Sometimes, you might need to amend a submitted change, for instance
when someone else does not approve your change by advising you to do it
differently or even when automatic tests run by Jenkins reports a negative vote
on your change. Then you need to amend your change. You can amend your own
changes as well as changes submitted by someone else, as long as the change
hasn't been merged yet.

You can checkout the change like this:

.. code-block:: bash

 git review -d {change number}

Note, if you already have the change in a branch on your local repository,
you can just check it out instead

.. code-block:: bash

 git checkout {branch-name}

After adding the necessary changes, amend the existing commit like this

.. code-block:: bash

 git commit --amend

NOTE: DO NOT use the -m flag to specify a commit summary: that will
override the previous summary and regenerate the Change-Id. Instead, use
your text editor to change the commit summary if needed, and keep
the Change-Id line intact.

Now, push the change using ``git review``


Review workflow
---------------

Software Factory mandates every patch to be reviewed before getting merged.


Who can review
..............

Anybody who is logged into Software Factory is eligible to review a patch
of any project except for private projects. Private projects can be
reviewed only by the team leads, developers, and core-developers of that
project.


How to review
.............

Ensure you are logged in to SF UI and select the patch you want to
review from the list of open patches. Following are some important files,
links and buttons that you need to be aware of.

**Reviewers**
  This field contains the list of reviewers for this patch. Getting into
  this list is as simple as posting a comment on the patch. Reviewers
  can be added by other parties or can be added voluntarily. The list of
  approvals given by a reviewer appears near their names.

  Following are the approvals

  - Verified
      Any rating in this means that the patch has been verified by compiling
      and running the test cases. This rate is given by a specific user
      called **Jenkins**. This rate is done automatically if automatic
      tests are configured for the related project.

  - Code-Review
      As the name implies, it contains the approvals for code review. Only
      **core-developers** can give '+2' for Code-Review

  - Workflow
      A '+1' in this means that this patch is approved for merging. Only
      **core-developers** can give '+1' for 'Workflow'
      A '0' in this means that this patch is ready for review.
      A '-1' in this means that this patch is in work in progress status.

**Add Reviewer**
  This button enables you to add new reviewers. As and when you enter a name
  you would given with a list of choices closer to your input.

**Dependencies**
  Often you would find a need to work on a patch based on a patch that is not
  merged yet. This field will let you know the list of patches that this patch
  depends on.

**Patch Sets**
  When a patch is committed for the first time, a 'Change-Id' is created. For
  further amendments to the patch, the 'Commit-Id' changes but the 'Change-Id'
  will not. Gerrit groups the patches and it's revisions based on this. This
  field lists all the revisions of the current change set and numbers them
  accordingly.

  Each and every patch set contains the list of files and their changes.
  Expand any patch set by clicking the arrow near it.

**Reference Version**
  When the review page is loaded, it expands just the last patch set, and will
  list down the changes that have been made on top of the parent commit
  (Base Version). This is the same with every patch set.

  In order to get the list of changes for say, patch set 11 from patch set 10,
  you need to select patch set 10 from the reference version.

**Changed items**
  When a patch set is expanded, it will list down the changed files. By clicking
  any file in this list will open a comparison page which will compare the
  changes of the selected patch set with the same file in the reference version.

  Upon clicking any line, a text box would be displayed with a 'Save' and 'Discard'
  buttons. 'Save' button saves the comment and maintains it in the databases.
  The comments will not be displayed unless you publish them.

**Abandon Change**
  At times, you might want to scrap an entire patch. The 'Abandon Change'
  button helps you to do that. The abandoned patches are listed separately from
  the 'Open' patch sets.

**Restore Change**
  Any abandoned patch can be restored back using this button. The 'Abandon Change'
  and 'Restore Change' buttons are mutually exclusive.

**Review**
  This is the actual button with which reviewers signal that the patch has been
  reviewed. Through this, you can also publish the list of your comments
  on the changes, give your score and, a cover message for the review.

  'Publish' button just publishes your review information. In addition to
  publishing, 'Publish and Submit' button also submits the change for merging.
  If there are enough scores to approve and if there are no conflicts seen
  while merging, Gerrit will rebase and merge the change on the master.


Approval Scoring
................

For any patch, following scores are need before a patch can be merged on the master
branch.

*Verified*
  At least one '+1' and no '-1'

*Code-Review*
  At least two '+2' (not cumulative) and no negative scoring.

*Workflow*
  At least one '+1'


.. _setup_ssh_keys:

Setting up SSH keys
-------------------

If the public key already exists, it will be listed in your .ssh
directory

.. code-block:: bash

 $ ls ~/.ssh/id_rsa.pub

In case you have the public key, you can skip to `Adding public key`_

You can generate a public key if you don't' have it already by
executing the following commands

.. code-block:: bash

 $ ssh-keygen -t rsa -C "your_email@your.domain"
 Generating public/private rsa key pair.
 Enter file in which to save the key (/home/you/.ssh/id_rsa):

Then you will be asked enter an optional passphrase. After this
you have a public key generated at the patch you chose.


.. _`Adding public key`:

Adding a public key
...................

Click on your username in the top right corner of the Gerrit UI,
then choose "Settings". On the left you will see SSH PUBLIC KEYS. Paste your
SSH Public Key into the corresponding field.
