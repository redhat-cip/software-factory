# Manage-sf
'manage-sf' is a REST based utility to create and delete projects in gerrit as well as redmine.

# How to use

Update config.py and execute the following commands, to use it for development purpose

* virtualenv venv
* . venv/bin/activate
* pip install -r requirements.txt
* pecan serve config.py

To deploy in production

* Refer pecan [dox](http://pecan.readthedocs.org/en/latest/deployment.html#deployment)

# URLs

## PUT
Creates a project.

### Usage
PUT /project/project-name

Information related to <project-name> are uploaded as a JSON data

#### Input Data

    {
        "description": A breif description about the project,
        "upstream": Upstream GIT URL from which the new project will be initialized,
        "ptl-group-members": Project team lead members,
        "core-group-members": Core group members
    }

If the no input data is uploaded, the new project will be created with empty description, empty repo, and the user requesting as the core and ptl group member

#### Headers
HTTP Basic Authorization header is mandatory

## DELETE
Deletes a project

### Usage
DELETE /project/project-name

### Headers 
HTTP Basic Authorization header is mandatory
