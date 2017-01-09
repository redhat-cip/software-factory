#!/usr/bin/python
# Licensed under the Apache License, Version 2.0
#
# Generate ansible group vars based on refarch and sfconfig.yaml

import argparse
import os
import yaml
import uuid


def append_legacy(allvars_file, args):
    """ Add bulk legacy vars to support smooth transition """
    allvars_file.write("###### Legacy content ######\n")
    allvars_file.write(open(args.sfconfig).read())
    allvars_file.write(open(args.sfcreds).read())
    allvars_file.write(open(args.arch).read())
    if os.path.isfile(args.extra):
        allvars_file.write(open(args.extra).read())


def yaml_load(filename):
    try:
        return yaml.safe_load(open(filename))
    except IOError:
        return {}


def yaml_dump(content, fileobj):
    yaml.dump(content, fileobj, default_flow_style=False)


def get_sf_version():
    return filter(lambda x: x.startswith("VERS="),
                  open("/var/lib/edeploy/conf").readlines()
                  )[0].strip().split('-')[1]


def generate_role_vars(allvars_file, args):
    """ This function 'glue' all roles and convert sfconfig.yaml """
    secrets = yaml_load("%s/secrets.yaml" % args.lib)
    arch = yaml_load(args.arch)
    sfconfig = yaml_load(args.sfconfig)

    # Generate all variable when the value is CHANGE_ME
    defaults = {}
    for role in arch["roles"]:
        role_vars = yaml_load("%s/roles/sf-%s/defaults/main.yml" % (
                              args.ansible_root, role))
        defaults.update(role_vars)
        for key, value in role_vars.items():
            if str(value).strip().replace('"', '') == 'CHANGE_ME':
                if key not in secrets:
                    secrets[key] = str(uuid.uuid4())

    # Generate dynamic role variable in the glue dictionary
    glue = {'mysql_databases': {}}

    def get_hostname(role):
        if len(arch["roles"][role]) != 1:
            raise RuntimeError("Role %s is defined on multi-host" % role)
        return arch["roles"][role][0]["hostname"]

    glue["gateway_url"] = "https://%s" % sfconfig["fqdn"]
    glue["sf_version"] = get_sf_version()

    if sfconfig["debug"]:
        for service in ("managesf", "zuul", "nodepool"):
            glue["%s_loglevel" % service] = "DEBUG"
            glue["%s_root_loglevel" % service] = "INFO"

    if "mysql" in arch["roles"]:
        glue["mysql_host"] = get_hostname("mysql")

    if "cauth" in arch["roles"]:
        glue["cauth_mysql_host"] = get_hostname("mysql")
        glue["mysql_databases"]["cauth"] = {
            'hosts': ['localhost', get_hostname("cauth")],
            'user': 'cauth',
            'password': secrets['cauth_mysql_password'],
        }

    if "managesf" in arch["roles"]:
        glue["managesf_internal_url"] = "http://%s:%s" % (
            get_hostname("managesf"), defaults["managesf_port"])
        glue["managesf_mysql_host"] = get_hostname("mysql")
        glue["mysql_databases"]["managesf"] = {
            'hosts': ['localhost', get_hostname("managesf")],
            'user': 'managesf',
            'password': secrets['managesf_mysql_password'],
        }

    if "gerrit" in arch["roles"]:
        glue["gerrit_pub_url"] = "%s/r/" % glue["gateway_url"]
        glue["gerrit_internal_url"] = "http://%s:%s/r/" % (
            get_hostname("gerrit"), defaults["gerrit_port"])
        glue["gerrit_email"] = "gerrit@%s" % sfconfig["fqdn"]
        glue["gerrit_mysql_host"] = glue["mysql_host"]
        glue["mysql_databases"]["gerrit"] = {
            'hosts': list(set(('localhost',
                               get_hostname("gerrit"),
                               get_hostname("managesf")))),
            'user': 'gerrit',
            'password': secrets['gerrit_mysql_password'],
        }

    if "zuul" in arch["roles"]:
        glue["zuul_pub_url"] = "%s/zuul/" % glue["gateway_url"]
        glue["zuul_internal_url"] = "http://%s:%s/" % (
            get_hostname("zuul"), defaults["zuul_port"])

    if "nodepool" in arch["roles"]:
        glue["nodepool_mysql_host"] = glue["mysql_host"]
        glue["mysql_databases"]["nodepool"] = {
            'hosts': ["localhost", get_hostname("nodepool")],
            'user': 'nodepool',
            'password': secrets['nodepool_mysql_password'],
        }

    if "jenkins" in arch["roles"]:
        glue["jenkins_host"] = get_hostname("jenkins")
        glue["jenkins_internal_url"] = "http://%s:%s/jenkins/" % (
            get_hostname("jenkins"), defaults["jenkins_http_port"])
        glue["jenkins_api_url"] = "http://%s:%s/jenkins/" % (
            get_hostname("jenkins"), defaults["jenkins_api_port"])
        glue["jenkins_pub_url"] = "%s/jenkins/" % glue["gateway_url"]

    if "redmine" in arch["roles"]:
        glue["redmine_internal_url"] = "http://%s:%s/" % (
            get_hostname("redmine"), defaults["redmine_port"])
        glue["redmine_pub_url"] = "%s/redmine/" % glue["gateway_url"]
        # Make sure api key doesn't have any '-'
        secrets["redmine_api_key"] = secrets["redmine_api_key"].replace('-',
                                                                        '')
        glue["redmine_mysql_host"] = get_hostname("mysql")
        glue["mysql_databases"]["redmine"] = {
            'hosts': list(set(('localhost',
                               get_hostname("redmine"),
                               get_hostname("managesf")))),
            'user': 'redmine',
            'password': secrets['redmine_mysql_password'],
        }

    if "grafana" in arch["roles"]:
        glue["grafana_internal_url"] = "http://%s:%s/" % (
            get_hostname("grafana"), defaults["grafana_http_port"])
        glue["grafana_mysql_host"] = get_hostname("mysql")
        glue["mysql_databases"]["grafana"] = {
            'hosts': ['localhost', get_hostname("grafana")],
            'user': 'grafana',
            'password': secrets['grafana_mysql_password'],
        }

    if "lodgeit" in arch["roles"]:
        glue["lodgeit_mysql_host"] = get_hostname("mysql")
        glue["mysql_databases"]["lodgeit"] = {
            'hosts': ['localhost', get_hostname("lodgeit")],
            'user': 'lodgeit',
            'password': secrets['lodgeit_mysql_password'],
        }

    if "etherpad" in arch["roles"]:
        glue["etherpad_mysql_host"] = get_hostname("mysql")
        glue["mysql_databases"]["etherpad"] = {
            'hosts': ['localhost', get_hostname("etherpad")],
            'user': 'etherpad',
            'password': secrets['etherpad_mysql_password'],
        }

    if "storyboard" in arch["roles"]:
        glue["storyboard_mysql_host"] = glue["mysql_host"]
        glue["mysql_databases"]["storyboard"] = {
            'hosts': ["localhost", get_hostname("storyboard")],
            'user': 'storyboard',
            'password': secrets["storyboard_mysql_password"],
        }

    # Save secrets to new secrets file
    yaml_dump(secrets, open("%s/secrets.yaml" % args.lib, "w"))
    # And add them to the all.yaml file
    yaml_dump(secrets, allvars_file)
    # Add glue to the all.yaml.file
    yaml_dump(glue, allvars_file)


def usage():
    p = argparse.ArgumentParser()
    p.add_argument("--ansible_root", default="/etc/ansible")
    p.add_argument("--arch", default="/etc/software-factory/_arch.yaml")
    p.add_argument("--sfconfig", default="/etc/software-factory/sfconfig.yaml")
    p.add_argument("--sfcreds", default="/etc/software-factory/sfcreds.yaml")
    p.add_argument("--extra", default="/etc/software-factory/custom-vars.yaml")
    p.add_argument("--lib", default="/var/lib/software-factory/bootstrap-data")
    return p.parse_args()


def main():
    args = usage()

    allyaml = "%s/group_vars/all.yaml" % args.ansible_root
    for dirname in ("%s/group_vars" % args.ansible_root, args.lib):
        if not os.path.isdir(dirname):
            os.makedirs(dirname, 0700)
    # Remove previously created link to sfconfig.yaml
    if os.path.islink(allyaml):
        os.unlink(allyaml)

    with open(allyaml, "w") as allvars_file:
        generate_role_vars(allvars_file, args)
        append_legacy(allvars_file, args)
    print("%s written!" % allyaml)


if __name__ == "__main__":
    main()
