#!/usr/bin/python

import os
import subprocess
import time

EXCLUDE_PATH = "/var/lib/sf"
IDS = '/etc/ids.tables'
uids, gids = None, None
try:
    exec(open(IDS).read())
except IOError:
    raise


def execute(cmd):
    print "Info: running %s" % str(cmd)
    ret = subprocess.Popen(cmd).wait()
    if ret:
        print "Warning: command failed"
    return ret


def update_uid(src, dst):
    execute(["find", "/", "-xdev", "-uid", str(src), "-exec",
             "chown", "-h", str(dst), "{}", ";"])


def update_gid(src, dst):
    execute(["find", "/", "-xdev", "-gid", str(src), "-exec",
             "chgrp", "-h", str(dst), "{}", ";"])


def update(ids_list, localname):
    localid = open("/etc/%s" % localname).readlines()
    dirty = False
    for id_name, ids in ids_list.items():
        # For each elem in ids.tables
        for idx in xrange(len(localid)):
            # For each elem in /etc/(passwd|group)
            pwd = localid[idx].split(':')

            if len(pwd) < 3:
                print "Invalid line [%s]" % localid[idx][:-1]
                continue

            if pwd[0] != id_name:
                # User defined in ids.tables not present in /etc/
                continue

            if pwd[1] != "x":
                print "Warning: %s has a password, removing it"
                pwd[1] = 'x'
                localid[idx] = ":".join(pwd)
                dirty = True

            wanted = "%s:x:%s:%s" % (id_name, ids[0], ids[1])
            if ids[1]:
                wanted += ':'
            # Check for uid/gid mismatch
            if localid[idx].startswith(wanted):
                if "DEBUG" in os.environ:
                    print "Debug: %s: %s is correct (%s == %s)" % (
                        localname, id_name, wanted, localid[idx][:-1])
                continue
            print "Info: %s: %s is not correct (%s != %s)" % (
                localname, id_name, wanted, localid[idx][:-1])
            if ids[1]:
                update_uid(pwd[2], ids[0])
                pwd[3] = ids[1]
            else:
                update_gid(pwd[2], ids[0])
            pwd[2] = ids[0]
            localid[idx] = ":".join(pwd)
            dirty = True

    if dirty:
        open("/etc/%s.orig" % localname, "w").write(
            open("/etc/%s" % localname).read())
        open("/etc/%s" % localname, "w").write("".join(localid))
        print "Info: Updated /etc/%s (original copied to /etc/%s.org" % (
            localname, localname)


def hide_sf():
    if (not os.path.isdir(EXCLUDE_PATH) or
            EXCLUDE_PATH in open("/proc/mounts").read()):
        return
    subprocess.Popen(["mount", "-t", "tmpfs", "none", EXCLUDE_PATH]).wait()


def unhide_sf():
    if EXCLUDE_PATH not in open("/proc/mounts").read():
        return
    subprocess.Popen(["umount", "/var/lib/sf"]).wait()


def main():
    print "%s: Starting uid-gid update" % time.ctime()
    hide_sf()
    update(uids, "passwd")
    update(gids, "group")
    unhide_sf()
    print "%s: uid-gid completed" % time.ctime()

main()
