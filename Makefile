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

ROLES = jenkins

all: $(ROLES)

jenkins: $(INST)/jenkins.done
$(INST)/jenkins.done: jenkins.install $(INST)/base.done
	./jenkins.install $(INST)/base $(INST)/jenkins $(VERS)
	touch $(INST)/jenkins.done

redmine: $(INST)/redmine.done
$(INST)/redmine.done: redmine.install $(INST)/base.done
	./redmine.install $(INST)/base $(INST)/redmine $(VERS)
	touch $(INST)/redmine.done

dist:
	tar zcvf ../edeploy-roles.tgz Makefile README.rst *.install *.exclude

clean:
	-rm -f *~ $(INST)/*.done

distclean: clean
	-rm -rf $(INST)/*

version:
	@echo "$(VERS)"

.PHONY: jenkins dist clean distclean version
