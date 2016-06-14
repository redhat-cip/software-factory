#!/bin/env python
import socket
import os
import sys
import time

if "--daemon" in sys.argv:
    # micro-deamon
    if os.fork() > 0 or os.fork() > 0:
        exit(0)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('localhost', 6667))
s.listen(1)
log = open("/var/log/fakeircd.log", "a")
while True:
    conn, addr = s.accept()
    log.write("%s: New connection from %s\n" % (time.ctime(), addr))
    if os.fork() == 0:
        nick = ''
        while 1:
            data = conn.recv(4096)
            if not data:
                break
            for line in data.split('\n'):
                if not line:
                    continue
                log.write("%s: %d - %s\n" % (time.ctime(), addr[1], line))
                log.flush()
                if line.startswith("NICK "):
                    nick = line.split()[-1]
                    conn.sendall(":locahost 001 %s Welcome\n" % nick)
                if line.startswith("JOIN "):
                    conn.sendall(":%s JOIN :%s\n" % (nick, line.split()[-1]))
        exit(0)
