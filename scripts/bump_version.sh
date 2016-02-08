#!/bin/bash
#
# How-to release a new version of SF:
#
#  1/ First edit role_configrc to set new and previous version strings:
# VER=2.1.6
# SF_PREVIOUS_VER=C7.0-2.1.5
#
#  2/ Commit using 'TaggedRelease: 2.1.5' (the actual release version, not the VER)
#  3/ Run this script to update references
#  4/ Check subproject history + sf history to update changelog
#  5/ Generate changelog with "reno report ." and copy the output to the CHANGELOG file
#     reno use a tag to compute the release version, remember to update version acording 'TaggedRelease' number in the CHANGELOG file.
#  6/ Commit --amend with all changes and new symlinks
#  7/ Wait for change to be merged (ask for review, recheck gate)
#  8/ Test new releases (either deploy or upgrade), in particular the changelog
#  9/ If published build is good, sign and re-publish the digest
#     gpg -u release@softwarefactory-project.io --clearsign softwarefactory-C7.0-${VER}.digest
#     mv softwarefactory-C7.0-${VER}.digest.asc softwarefactory-C7.0-${VER}.digest
#     publish softwarefactory-C7.0-${VER}.digest to swift
# 10/ Generate package diff: diff previous_release.description new_release.description
# 11/ Prepare mail, see previous announcement for template (re-use doug famous introduction from http://lists.openstack.org/pipermail/openstack-announce/)
# 12/ Tag: git tag -s -a -m "${VER}" ${VER} HEAD
# 13/ Submit tag: git push --tags gerrit
# 14/ Send announcement
#
. ./role_configrc

DEPS='/var/lib/sf/deps'

if [ "${TAGGED_RELEASE}" != "1" ]; then
    echo Run this script on a TaggedRelease: commit only
    exit 1
fi

# Read next version number directly to avoid CommitTag auto-change
NEW_VER="C7.0-$(grep ^VER role_configrc | cut -d= -f2)"

# Create new update path
echo "## Metadata path..."
echo "# Maintain old stable to current path"
for i in image/metadata/C7.0-2.0*/softwarefactory/C7.0-*; do
    echo git mv $i $(dirname $i)/${SF_VER}
done
echo "# Create new path"
echo mkdir -p image/metadata/${SF_VER}/softwarefactory
for i in image/metadata/C7.0-2.1*/softwarefactory/; do
    echo ln -s ../../metadata_2x/ ${i}/${NEW_VER}
done
echo ln -s ../../metadata_2x/ image/metadata/${SF_VER}/softwarefactory/${NEW_VER}
echo git add image/metadata

echo
echo "## Upgrade path..."
echo "# Maintain Upgrade path for stable"
for i in upgrade/C7.0-2.0*/*; do
    echo git mv $i $(dirname $i)/${SF_VER}
done
echo "# Create new path"
echo mkdir -p upgrade/${SF_VER}
for i in upgrade/C7.0-2.1*/; do
    echo ln -s ../upgrade_2x/ ${i}/${NEW_VER}
done
echo ln -s ../upgrade_2x/ upgrade/${SF_VER}/${NEW_VER}
echo git add upgrade
echo

# Change README
echo "## Documentation"
PREV_STABLE=$(grep "^The last stable" README.md | awk '{ print $6 }')
echo sed -i README.md -e "s/${SF_VER}/${NEW_VER}/g" -e "s/${PREV_STABLE}/${VER}/"
echo git add README.md
echo
echo "## Fetching subproject"
# Check subprojects origin/master
for i in pysflib managesf python-sfmanager cauth; do
    (cd ${DEPS}/$i; git fetch origin &> /dev/null)
    PINNED_VERSION=$(cat ${DEPS}/$i/.git/FETCH_HEAD | awk '{ print $1 }')
    VNAME="$(echo $i | tr '[:lower:]' '[:upper:]')_PINNED_VERSION"
    echo sed -i role_configrc -e \"s/${VNAME}=.*/${VNAME}=${PINNED_VERSION}/\"
done
echo git add role_configrc

echo git commit -a --amend
