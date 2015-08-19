#!/bin/bash

# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


# This script is used to get and export a Software Factory backup
# and export it to a Swift container. To automate the run you may
# setup a cron job


[ -n "$DEBUG" ] && set -x
set -e

. /etc/auto_backup.conf

# Exit silently if we don"t have enough OS_* env vars
[ -z "$OS_AUTH_URL" ] && exit 0
[ -z "$OS_TENANT_NAME" ] && exit 0
[ -z "$OS_USERNAME" ] && exit 0
[ -z "$OS_PASSWORD" ] && exit 0

# Exit silently if we don"t have enough BACKUP_* env vars
[ -z "$BACKUP_CONTAINER" ] && exit 0
[ -z "$BACKUP_RET" ] && exit 0

SWIFT_CONTAINER=${BACKUP_CONTAINER}
RETENTION_SECS=${BACKUP_RET}

epoch=$(date +%s)

echo "Backup started at ${epoch}."

# Create the container if not exists
if ! swift stat $SWIFT_CONTAINER &> /dev/null; then
    echo "Create container $SWIFT_CONTAINER."
    swift post $SWIFT_CONTAINER
fi

# Clean old backups if needed
backups=$(swift list $SWIFT_CONTAINER | sort)
echo "Container $SWIFT_CONTAINER has $(echo $backups | wc -w) backups before deletion."
for backup in $backups; do
    upload_date=$(swift stat $SWIFT_CONTAINER $backup | grep X-Timestamp | cut -d":" -f 2)
    upload_date=$(echo $upload_date | cut -d"." -f 1)
    if [ $((epoch - upload_date)) -gt $RETENTION_SECS ]; then
        echo "Backup $backup is too old according to the retention value. Delete it."
        swift delete $SWIFT_CONTAINER $backup &> /dev/null
    fi
done

# Get SF backup via managesf
sfmanager --url http://$HOST --auth $ADMIN:$ADMIN_PASSWORD backup start
sfmanager --url http://$HOST --auth $ADMIN:$ADMIN_PASSWORD backup get
mv sf_backup.tar.gz /tmp/sf_backup.tar.gz
# Upload backup
swift upload $SWIFT_CONTAINER /tmp/sf_backup.tar.gz --object-name sf_backup_${epoch}.tar.gz &> /dev/null
if [ "$?" != "0" ]; then
    echo "Error when uploading the backup sf_backup_${epoch}.tar.gz in container $SWIFT_CONTAINER ! exit."
    exit 1
fi
echo "sf_backup_${epoch}.tar.gz has been uploaded."
