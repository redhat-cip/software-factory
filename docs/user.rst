Contents:

.. toctree::

Using the Software factory
==========================

Create a project
----------------
Any user can create a project. (See :ref:`managesf_create_project`)


How to contribute
-----------------

Central Source code repository
------------------------------
Softwarefactory uses `GIT <http://en.wikipedia.org/wiki/Git_%28software%29>`_
as its revision control system. As and when a project is created, Gerrit
initializes the projects' repository.
The repositories can be `cloned <http://git-scm.com/docs/git-clone>`_ from
the gerrit server to a local directory. Gerrit allows multiple ways to clone
any projects' repositories.

- http
    ::

      http://{gerrit-host}/r/{project-name}

- SSH
    Before accessing SSH url, one needs to register the SSH public key of
    the computer where the project wants to be cloned. (See :ref:`setup_ssh_keys`)

    ::

      ssh://{user-name}@{gerrit-host}:29418/{project-name}


Preparing the local repository
------------------------------

In order to work with gerrit, you need to add a "change id" to your commit summary
(you can see these if you browse changes on gerrit, they look like

  ::

    Change-Id: Ibd3be19ed1a23c8638144b4a1d32f544ca1b5f97

Each time you amend a commit in response to gerrit feedback git gives it a new
commit ID, but because this change ID stays the same gerrit will keep track of
it as a new "patch set" addressing the same change

Installing git-review
.....................

git-review is a git add-on that manages the reviewing and other aspects of gerrit

Generally, the easiest way to get last version is to install it using the python
package installer pip

.. code-block:: bash

    $ sudo pip install git-review


Setting up git-review
......................

You have to setup the local repo for git-review before commiting any
changes to it.
Make sure you have installed your ssh keys to gerrit (See :ref:`setup_ssh_keys`)

  ::

    git review -s

It will prompt you to enter a user name. This user name will be list as the
author of the commit.

Submitting a patch
------------------

Before starting to work its a good practise to setup a branch and work on it.
The branch name will be displayed as the topic for the patch(es) you are going
to create from it, so give it a meaningful name like bug/{bug-id},
title-bug-fix, ...

To create a branch

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

Publishing the change
.....................

Before your changes can be merged into master, they must undergo review in Gerrit

But first, it's a good idea to synchronize your change set with any changes that
may have occurred in master while you've been working. From within the branch
you've been working on, execute the following command:

  ::

    git pull --rebase origin master

This command will fetch new commits from the remote and then rebase your local
commits on top of them. It will temporarily set aside the changes you've made
in your branch, apply all of the changes that have happend in master to your
working branch, then merge (recommit) all of the changes you've made back into
the branch. Doing this will help avoid future merge conflicts. Plus, it gives
you an opportunity to test your changes against the latest code in master

Once you are satisfied with your change set and you've rebased against master,
you are ready to push your code to Gerrit for review.

Make sure you had setup git-review before submitting the code for review.

To push the chage to gerrit, execute the following command

.. code-block:: bash

    $ git review
    # remote: Processing changes: new: 1, refs: 1, done
    # remote:
    # remote: New Changes:
    # remote:   http://{gerrit-host}/{change-number}
    # remote:
    # To ssh://{user-name}@{gerrit-host}:29418/{project-name}
    #  * [new branch]      HEAD -> refs/publish/master/branch-name

Amending a change
.................

Sometimes, you might need to amend a submitted change. You can amend your own
changes as well as changes submitted by someone else, as long as the change
hasn't been merged yet.

Checkout the change like this

  ::

    git review -d {change number}

Note, if you already have the change in a branch on your local repository,
you can just check it out instead

  ::

    git checkout {branch-name}

After adding the necessary changes, amend the existing commit like this

  ::

    git commit --amend

NOTE: DO NOT use the -m flag to specify a commit summary: that will
override the previous summary and regenerate the Change-Id. Instead, use
your text editor to change the commit summary if needed, and keep
the Change-Id line intact.

Now, push the change using ``git review``


Reviewing workflow
------------------

Softwarefactory mandates every patch to be reviewed before getting merged.


Who can review
..............

Anybody who are logged in to softwarefactory are eligible to review a patch
of any project except the private projects. The private projects can be
reviewed only by the team leads, developers, and core-developers of that
project.


How to review
.............

Ensure you are logged in to softwarefactory. Select the patch you want to
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
      and running the test cases.

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
  merged yet. This field will let you know the list of patch that this patch
  depends on.

**Patch Sets**
  When a patch is commited for the first time, a 'Change-Id' is created. For
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
  any file in this list will open a comparision page which will compare the
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
  This is the actual button with which reviwers signal that the patch has been
  reviewed. Through this, you can also publish the list of your comments
  on the changes, give your score and, a cover message for the review.

  'Publish' button just publishes your review information. In addition to
  publishing, 'Publish and Submit' button also submits the change for merging.
  If there are enough scores to approve and if there are no conflicts seen
  while merging, gerrit will rebase and merge the change on the master.


Approval Scoring
................

For any patch, following scores are need

*Verfied*
  At leat one '+1' and no '-1'

*Code-Review*
  At least two '+2' (not cummulative) and no negative scoring.

*Workflow*
  At least one '+1'


.. _setup_ssh_keys:

Setting up SSH keys
-------------------

If the public key alreadys exists, it will be listed in your .ssh
directory

.. code-block:: bash

  $ ls ~/.ssh/id_rsa.pub

In case you have the public key, you can skip to `Adding public key`_

You can generate a public key if you dont' have it already by
executing the following commands

.. code-block:: bash

   $ ssh-keygen -t rsa -C "your_email@your.domain"
   Generating public/private rsa key pair.
   Enter file in which to save the key (/home/you/.ssh/id_rsa):

Then you will be asked enter an optional passphrase. After this
you have a public key generated at the patch you chose.

Then add your new key to the ssh-agent

.. code-block:: bash

  # start the ssh-agent in the background
  $ eval `ssh-agent -s`
  # Agent pid 59566
  $ ssh-add ~/.ssh/id_rsa

.. _`Adding public key`:

Adding public key
.................

Run the following code to copy the key to your clipboard.

.. code-block:: bash

  $ sudo apt-get install xclip
  # Downloads and installs xclip. If you don't have `apt-get`, you might need to use another installer (like `yum`)
  $ xclip -sel clip < ~/.ssh/id_rsa.pub
  # Copies the contents of the id_rsa.pub file to your clipboard

Click on your username in the top right corner, then choose "Settings".
On the left you will see SSH PUBLIC KEYS. Paste your SSH Public Key
into the corresponding field.
