socat TCP-LISTEN:80,fork TCP:sf-gerrit:80 &
socat TCP-LISTEN:81,fork TCP:sf-redmine:80 &
socat TCP-LISTEN:8080,fork TCP:sf-jenkins:8080 &
