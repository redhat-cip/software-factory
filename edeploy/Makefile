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

DVER=D7

# Prevent edeploy from building .edeploy files (no more pigz/gzip)
STRIPPED_TARGET=false

ARCH=amd64
export PATH := /sbin:/bin::$(PATH)

MAKEFILE_TARGET=$(MAKECMDGOALS)
CURRENT_TARGET=$@
export MAKEFILE_TARGET
export CURRENT_TARGET

SF_VERSION=$(DVER)-$(SF_REL)
EDEPLOY_VERSION=$(EDEPLOY_REL)

INST=$(TOP)/install/$(SF_VERSION)
EDR_INST=$(TOP)/install/$(PREBUILD_EDR_TARGET)

ROLES = install-server-vm softwarefactory

all: $(ROLES)

softwarefactory: $(INST)/softwarefactory.done
$(INST)/softwarefactory.done: softwarefactory.install $(EDR_INST)/cloud.done
	rm -f $(INST)/softwarefactory-*.img*
	@(echo "----| Building softwarefactory role |----")
	./softwarefactory.install $(EDR_INST)/cloud $(INST)/softwarefactory $(SF_VERSION)
	touch $(INST)/softwarefactory.done

install-server-vm: $(INST)/install-server-vm.done
$(INST)/install-server-vm.done: install-server-vm.install $(EDR_INST)/install-server.done
	rm -f $(INST)/install-server-vm-*.img*
	@(echo "----| Building install-server-vm |----")
	./install-server-vm.install $(EDR_INST)/install-server $(INST)/install-server-vm $(SF_VERSION)
	touch $(INST)/install-server-vm.done

dist:
	tar zcvf ../edeploy-roles.tgz Makefile README.rst *.install *.exclude

clean:
	-for f in $(ROLES); do rm -rf $(INST)/$$f;done

distclean: clean
	-for f in $(ROLES); do rm -rf $(INST)/$$f*; done

version:
	@echo "$(SF_VERSION)"

.PHONY: bootstrapper install-server-vm softwarefactory dist clean distclean version
