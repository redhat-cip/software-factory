edeploy-software-factory-roles
==============================

The edeploy roles for software factory roles.

Creating a bootable image
-------------------------

You need a configuration file for creating bootable images. For example:

	# Size of the root filesystem in MB or auto
	#ROOT_FS_SIZE=1000
	ROOT_FS_SIZE=auto

	# Output format supported by qemu-img
	# Use 'qemu-img --help | grep Supported | cut -d ":" -f2' to get the full list
	IMAGE_FORMAT=qcow2

	# Network Configuration
	# Only auto is supported now
	NETWORK_CONFIG=auto

Save this as "jenkings.virt". Now create an image:

	sudo make jenkins VIRTUALIZED=jenkins.virt

The image will be saved as `/var/lib/debootstrap/install/D7-H.1.0.0/jenkins-D7-H.1.0.0.img.vdi`.


