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

Save this as "jenkins.virt". Now create an image:

	sudo make jenkins VIRTUALIZED=jenkins.virt

The image will be saved as `/var/lib/debootstrap/install/D7-H.1.0.0/jenkins-D7-H.1.0.0.img.qcow2`.

Registering image and booting VM
--------------------------------

1. Upload images to Glance (set OS_* before)

	glance -v image-create --name="eDeploy MySQL" --container-format ovf --disk-format qcow2 < /var/lib/debootstrap/install/D7-H.1.0.0/mysql-D7-H.1.0.0.img.qcow2 
	glance -v image-create --name="eDeploy Redmine" --container-format ovf --disk-format qcow2 < /var/lib/debootstrap/install/D7-H.1.0.0/redmine-D7-H.1.0.0.img.qcow2

2. Get image UUIDs:

	nova image-show "eDeploy MySQL"
	nova image-show "eDeploy Redmine"

3. Add required users and databases to mysql.cloudinit

4. Start new VM using MySQL image:

 	nova boot --flavor 10 --image 0c9dfe66-2be7-46f8-90cf-dc2116df49be --user-data mysql.cloudinit --key_name cschwede edeploy-mysql

5. Get private IP from machine:

	nova show "edeploy-mysql"

6. Update private IP in redmine.cloudinit

7. Start new VM using Redmine image:
	
	nova boot --flavor 10 --image 34e66e87-00a5-4852-ada8-8ac31d557c3e --user-data redmine.cloudinit --key_name cschwede --security-groups default,public-web edeploy-redmine

8. Assign floating IP to redmine VM:

	nova floating-ip-associate edeploy-redmine 198.154.188.219
