#!/bin/bash
TIMESTAMP=`date +"%Y%m%d"`
mysqldump --all-databases -u root -pyour_password > /root/$TIMESTAMP-dump.sql
