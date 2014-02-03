#
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Frederic Lepied <frederic.lepied@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Exporting ALL variables to other childs
.EXPORT_ALL_VARIABLES:

MAKEFILE_DIR=$(shell pwd)
SDIR=/srv/edeploy
TOP=/var/lib/debootstrap
ARCHIVE=/var/cache/edeploy-roles
DVER=D7
PVER=H
REL=1.0.0
VERSION:=$(PVER).$(REL)
VERS=$(DVER)-$(VERSION)
DIST=wheezy

ARCH=amd64
export PATH := /sbin:/bin::$(PATH)

MAKEFILE_TARGET=$(MAKECMDGOALS)
CURRENT_TARGET=$@
export MAKEFILE_TARGET
export CURRENT_TARGET

INST=$(TOP)/install/$(VERS)
META=$(TOP)/metadata/$(VERS)

ROLES = jenkins gerrit redmine mysql ldap

# Build virtual images by default
export VIRTUALIZED=params.virt

all: $(ROLES)

jenkins: $(INST)/jenkins.done
$(INST)/jenkins.done: jenkins.install $(INST)/vm.done
	./jenkins.install $(INST)/vm $(INST)/jenkins $(VERS)
	touch $(INST)/jenkins.done

ldap: $(INST)/ldap.done
$(INST)/ldap.done: ldap.install $(INST)/vm.done
	./ldap.install $(INST)/vm $(INST)/ldap $(VERS)
	touch $(INST)/ldap.done

gerrit: $(INST)/gerrit.done
$(INST)/gerrit.done: gerrit.install $(INST)/vm.done
	./gerrit.install $(INST)/vm $(INST)/gerrit $(VERS)
	touch $(INST)/gerrit.done

redmine: $(INST)/redmine.done
$(INST)/redmine.done: redmine.install $(INST)/vm.done
	./redmine.install $(INST)/vm $(INST)/redmine $(VERS)
	touch $(INST)/redmine.done

mysql: $(INST)/mysql.done
$(INST)/mysql.done: mysql.install $(INST)/vm.done
	./mysql.install $(INST)/vm $(INST)/mysql $(VERS)
	touch $(INST)/mysql.done

vm: $(INST)/vm.done
$(INST)/vm.done: vm.install $(INST)/base.done
	./vm.install $(INST)/base $(INST)/vm $(VERS)
	touch $(INST)/vm.done

$(INST)/base.done:
	mkdir -p $(INST)/base
	tar zxf $(ARCHIVE)/$(VERS)/base-$(VERS).edeploy -C $(INST)/base
	touch $(INST)/base.done

dist:
	tar zcvf ../edeploy-roles.tgz Makefile README.rst *.install *.exclude

clean:
	-for f in $(ROLES); do rm -rf $(INST)/$$f;done

distclean: clean
	-for f in $(ROLES); do rm -rf $(INST)/$$f*; done

version:
	@echo "$(VERS)"

.PHONY: jenkins ldap gerrit redmine mysql vm dist clean distclean version
