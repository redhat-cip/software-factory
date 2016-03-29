Rename a project on SF
======================

Add projects to rename there in rename-rules.yaml:

```YAML
repos:
- old: myproject
  new: mynewprojectname
- old: myproject2
  new: namespace/mynewprojectname2
```

Run:
ansible-playbook -i inventory rename_repos.yaml

Some tags are available to split renaming actions:
- project_rename: Rename project for Gerrit and Redmine
- test_triggers_rename: Update project name in zuul/projects.yaml
- replication_project_rename: Update project name/ssh config alias for replication

Create that file before on the managesf node /root/.my.cnf

[client]
user=root
password=<from sfcreds.yaml>
