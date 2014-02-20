#!/bin/bash
TIMESTAMP=`date +"%Y%m%d"`
slapcat > /root/$TIMESTAMP-dump.ldif
