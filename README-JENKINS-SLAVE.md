    dd if=/dev/zero of=swap count=4000 bs=1M
    mkswap swap
    swapon swap

# define hostname
    vi /etc/hostname
    hostname -F /etc/hostname

# configure sf.dom
    vi /etc/hosts

# install start script
   vi /etc/rc.local
        swapon /root/swap
        nohup sudo -u jenkins -i java -jar /var/lib/jenkins/swarm-client-1.15-jar-with-dependencies.jar -master http://sf.dom:8080/jenkins -username jenkins -password XXXXXX -name stronger-jenkins -labels func -mode exclusive -executors 1 &

# install deps
   apt-get install nginx
   apt-get install debootstrap
   apt-get install git vim gdb strace openjdk-7-jre git python-pip unzip pigz

# configure nginx
   vi /etc/nginx/sites-enabled/default
        server {
            listen   8081;

            root /var/lib/sf/artifacts;
            index index.html index.htm;

            server_name localhost;

            location / {
                autoindex on;
                default_type text/plain;
            }
        }

   service nginx reload

# add jenkins user
   useradd -s /bin/bash -d /var/lib/jenkins -r -m jenkins
   vi /etc/sudoers
        jenkins ALL=(ALL:ALL)  NOPASSWD: ALL

# install jenkins private key and authorized_keys
   #... (copy bigger-jenkins:~jenkins/.ssh )

# install swarm client
   curl -O http://maven.jenkins-ci.org/content/repositories/releases/org/jenkins-ci/plugins/swarm-client/1.15/swarm-client-1.15-jar-with-dependencies.jar

# Others deps:
   git clone https://github.com/enovance/edeploy-lxc.git   # cwd: /srv
   apt-get install python-augeas bridge-utils

# Install fbo-kernel to support lxc!!
   (use "echo b > /proc/sysrq-trigger" if reboot does not boot it)
# Generate ubuntu ssh key (used by edeploy-lxc)
   ubuntu # ssh-keygen

# Install LXC
   apt-get install libcap-dev
   http://ftp.de.debian.org/debian/pool/main/l/lxc/lxc_0.8.0~rc1.orig.tar.xz
   tar xJf lxc*.xz
   cd lxc*
   ./configure && make && make install
   ln -s /var /usr/local/
   echo none        /cgroup        cgroup        defaults    0    0 >> /etc/fstab

=> root@faster-jenkins:~# lxc-version
   lxc version: 0.8.0-rc1

# Patch edeploy-lxc with this:
diff --git a/edeploy-lxc b/edeploy-lxc
index 66cbc49..ea17c27 100755
--- a/edeploy-lxc
+++ b/edeploy-lxc
@@ -212,7 +212,7 @@ dsmod: local
 datasource_list: [ NoCloud ]
 ''')
         print("    launching")
-        subprocess.call(['lxc-start', '-d', '-L', '/tmp/lxc-%s.log' % host['name'], '-n', host['name'] ])
+        subprocess.call(['lxc-start', '-d', '-o', '/tmp/debug_%s' % host['name'], '-n', host['name'] ])

 parser = argparse.ArgumentParser()
 parser.add_argument('action', help='action', choices=['stop', 'start', 'restart'])

# reboot
