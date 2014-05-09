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

# Prevent edeploy from building .edeploy files (no more pigz/gzip)
STRIPPED_TARGET=false

ARCH=amd64
export PATH := /sbin:/bin::$(PATH)

MAKEFILE_TARGET=$(MAKECMDGOALS)
CURRENT_TARGET=$@
export MAKEFILE_TARGET
export CURRENT_TARGET

INST=$(TOP)/install/$(VERS)
META=$(TOP)/metadata/$(VERS)

ROLES = install-server-vm mysql ldap softwarefactory

all: $(ROLES)

softwarefactory: $(INST)/softwarefactory.done
$(INST)/softwarefactory.done: softwarefactory.install $(INST)/vm.done
	rm -f $(INST)/softwarefactory-$(DVER)-$(PVER).$(REL).img
	./softwarefactory.install $(INST)/vm $(INST)/softwarefactory $(VERS)
	touch $(INST)/softwarefactory.done

ldap: $(INST)/ldap.done
$(INST)/ldap.done: ldap.install $(INST)/vm.done
	rm -f $(INST)/ldap-$(DVER)-$(PVER).$(REL).img
	./ldap.install $(INST)/vm $(INST)/ldap $(VERS)
	touch $(INST)/ldap.done

mysql: $(INST)/mysql.done
$(INST)/mysql.done: mysql.install $(INST)/vm.done
	rm -f $(INST)/mysql-$(DVER)-$(PVER).$(REL).img
	./mysql.install $(INST)/vm $(INST)/mysql $(VERS)
	touch $(INST)/mysql.done

bootstrapper:
	./puppet_bootstrapper.sh

install-server-vm: $(INST)/vm.done bootstrapper
	rm -f $(INST)/install-server-vm-$(DVER)-$(PVER).$(REL).img
	./install-server-vm.install $(INST)/vm $(INST)/install-server-vm $(VERS)

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

.PHONY: bootstrapper install-server-vm ldap mysql softwarefactory vm dist clean distclean version 
