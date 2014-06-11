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
EDEPLOY_VERSION=D7-H.$(EDEPLOY_REL)

INST=$(TOP)/install/$(SF_VERSION)
E_INST=$(TOP)/install/$(EDEPLOY_VERSION)

ROLES = install-server-vm mysql slave ldap softwarefactory

all: $(ROLES)

softwarefactory: $(INST)/softwarefactory.done
$(INST)/softwarefactory.done: softwarefactory.install $(INST)/vm.done
	# FIXME: here we must use EDEPLOY_VERSION as it will failed on /srv/edeploy/build/functions: line 42
	# because /var/lib/sf/roles/install/D7-H.0.9.0/vm/var/lib/edeploy/D7-H.0.9.0/exclude
	# does not exists from base role
	./softwarefactory.install $(INST)/vm $(INST)/softwarefactory $(EDEPLOY_VERSION)
	touch $(INST)/softwarefactory.done

ldap: $(INST)/ldap.done
$(INST)/ldap.done: ldap.install $(INST)/vm.done
	./ldap.install $(INST)/vm $(INST)/ldap $(EDEPLOY_VERSION)
	touch $(INST)/ldap.done

mysql: $(INST)/mysql.done
$(INST)/mysql.done: mysql.install $(INST)/vm.done
	./mysql.install $(INST)/vm $(INST)/mysql $(EDEPLOY_VERSION)
	touch $(INST)/mysql.done

slave: $(INST)/slave.done
$(INST)/slave.done: slave.install $(INST)/vm.done
	./slave.install $(INST)/vm $(INST)/slave $(EDEPLOY_VERSION)
	touch $(INST)/slave.done

bootstrapper:
	./puppet_bootstrapper.sh

install-server-vm: $(INST)/vm.done bootstrapper
	./install-server-vm.install $(INST)/vm $(INST)/install-server-vm $(EDEPLOY_VERSION)

vm: $(INST)/vm.done
$(INST)/vm.done: vm.install $(E_INST)/base.done
	./vm.install $(E_INST)/base $(INST)/vm $(EDEPLOY_VERSION)
	touch $(INST)/vm.done

$(E_INST)/base.done:
	mkdir -p $(E_INST)/base
	touch $(E_INST)/base.done

dist:
	tar zcvf ../edeploy-roles.tgz Makefile README.rst *.install *.exclude

clean:
	-for f in $(ROLES); do rm -rf $(INST)/$$f;done

distclean: clean
	-for f in $(ROLES); do rm -rf $(INST)/$$f*; done

version:
	@echo "$(SF_VERSION)"

.PHONY: bootstrapper install-server-vm ldap mysql slave softwarefactory vm dist clean distclean version 
