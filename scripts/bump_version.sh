#!/bin/bash

. ./role_configrc

# Read next version number directly to avoid CommitTag auto-change
NEW_VER="C7.0-$(grep ^VER role_configrc | cut -d= -f2)"

# Create new update path
echo "## Metadata path..."
echo "# Maintain old stable to current path"
for i in image/metadata/C7.0-2.0*/softwarefactory/C7.0-*; do
    echo mv $i $(dirname $i)/${SF_VER}
done
echo "# Update prev version to new path"
for i in image/metadata/C7.0-2.1*/softwarefactory/C7.0-*; do
    echo mv $i $(dirname $i)/${NEW_VER}
done
echo "# Create new path"
echo mkdir -p image/metadata/${SF_VER}/softwarefactory
echo ln -s ../../metadata_2x/ image/metadata/${SF_VER}/softwarefactory/${NEW_VER}

echo "## Upgrade path..."
echo "# Maintain Upgrade path for stable"
for i in upgrade/C7.0-2.0*/*; do
    echo mv $i $(dirname $i)/${SF_VER}
done
echo "# Update prev verions"
for i in upgrade/C7.0-2.1*/*; do
    echo mv $i $(dirname $i)/${NEW_VER}
done
echo "# Create new path"
echo mkdir -p upgrade/${SF_VER}
echo ln -s ../upgrade_2x/ upgrade/${SF_VER}/${NEW_VER}


# Change README
echo "## Documentation"
PREV_STABLE=$(grep "^The last stable" README.md | awk '{ print $6 }')
echo sed -i README.md -e "s/${SF_VER}/${NEW_VER}/g" -e "s/${PREV_STABLE}/${VER}/"
echo sed
echo sed -i serverspec/hosts.yaml -e "s/${SF_VER}/${VER}/g"

# Check subprojects origin/master
for i in pysflib managesf python-sfmanager cauth; do
    (
        cd $i
        git fetch --all
        echo "${i}_PINNED_VERSION $(cat .git/refs/remotes/origin/master)"
    )
done

