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
SDIR=$(EDEPLOY_PATH)
TOP=/var/lib/debootstrap
ARCHIVE=/var/cache/edeploy-roles

DIST=wheezy

# Prevent edeploy from building .edeploy files (no more pigz/gzip)
STRIPPED_TARGET=false

ARCH=amd64
export PATH := /sbin:/bin::$(PATH)

MAKEFILE_TARGET=$(MAKECMDGOALS)
CURRENT_TARGET=$@
export MAKEFILE_TARGET
export CURRENT_TARGET

SF_VERSION=D7-H.$(SF_REL)
EDEPLOY_VERSION=$(EDEPLOY_REL)

INST=$(TOP)/install/$(SF_VERSION)
EDR_INST=$(TOP)/install/$(PREBUILD_EDR_TARGET)

ROLES = install-server-vm mysql slave ldap softwarefactory

all: $(ROLES)

softwarefactory: $(INST)/softwarefactory.done
$(INST)/softwarefactory.done: softwarefactory.install $(EDR_INST)/cloud.done
	rm -f $(INST)/softwarefactory-*.img*
	./softwarefactory.install $(EDR_INST)/cloud $(INST)/softwarefactory $(SF_VERSION)
	touch $(INST)/softwarefactory.done

ldap: $(INST)/ldap.done
$(INST)/ldap.done: ldap.install $(EDR_INST)/cloud.done
	rm -f $(INST)/ldap-*.img*
	./ldap.install $(EDR_INST)/cloud $(INST)/ldap $(SF_VERSION)
	touch $(INST)/ldap.done

mysql: $(INST)/mysql.done
$(INST)/mysql.done: mysql.install $(EDR_INST)/cloud.done
	rm -f $(INST)/mysql-*.img*
	./mysql.install $(EDR_INST)/cloud $(INST)/mysql $(SF_VERSION)
	touch $(INST)/mysql.done

slave: $(INST)/slave.done
$(INST)/slave.done: slave.install $(EDR_INST)/cloud.done
	rm -f $(INST)/slave-*.img*
	./slave.install $(EDR_INST)/cloud $(INST)/slave $(SF_VERSION)
	touch $(INST)/slave.done

bootstrapper:
	./puppet_bootstrapper.sh

install-server-vm: $(EDR_INST)/install-server.done bootstrapper
	rm -f $(INST)/install-server-vm-*.img*
	./install-server-vm.install $(EDR_INST)/install-server $(INST)/install-server-vm $(SF_VERSION)

dist:
	tar zcvf ../edeploy-roles.tgz Makefile README.rst *.install *.exclude

clean:
	-for f in $(ROLES); do rm -rf $(INST)/$$f;done

distclean: clean
	-for f in $(ROLES); do rm -rf $(INST)/$$f*; done

version:
	@echo "$(SF_VERSION)"

.PHONY: bootstrapper install-server-vm ldap mysql slave softwarefactory dist clean distclean version 
