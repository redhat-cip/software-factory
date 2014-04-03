#!/usr/bin/python

import unittest
import subprocess
import os
from redmine import Redmine
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from pygerrit.rest import GerritRestAPI


class Base(unittest.TestCase):
    pass

class Tool:
    cwd = "."
    def run(self, argv):
        old_cwd = os.getcwd()
        os.chdir(self.cwd)
        try:
            ret = subprocess.call([self.exe] + argv)
        finally:
            os.chdir(old_cwd)
        return ret

class ManageSf(Tool):
    cwd = "./tools/manage-sf"
    exe = "./manage"

class Git(Tool):
    exe = "/usr/bin/git"


class GerritUtil:
    def __init__(self, url, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password
        self.auth = None
        self.anonymous = False
        if username is None or password is None:
            self.anonymous = True
        if not self.anonymous:
            self.auth = HTTPBasicAuth(username, password)
        self.rest = GerritRestAPI(self.url, self.auth)

    # project APIs
    def getProjects(self, name=None):
        if name:
            return self.rest.get('/projects/%s' % name)
        else:
            return self.rest.get('/projects/?')

    def isPrjExist(self, name):
        try:
            p = self.getProjects(name)
            return p['name'] == name
        except HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                raise

    # Group APIs
    def isGroupExist(self, name):
        g = self.rest.get('/groups/')
        return name in g

    def getGroupOwner(self, name):
        g = self.rest.get('/groups/%s/owner' % name)
        return g['owner']

    def isMemberInGroup(self, username, groupName):
        try:
            g = self.rest.get('/groups/%s/members/%s' % (groupName, username))
            return (len(g) >= 1 and g['username'] == username)
        except HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                raise

    def addGroupMember(self, username, groupName):
        self.rest.put('/groups/%s/members/%s' % (groupName, username))

    def deleteGroupMember(self, username, groupName):
        self.rest.delete('/groups/%s/members/%s' % (groupName, username))

    # Review APIs
    def _submitCodeReview(self, change_id, revision_id, rate):
        reviewInput = {"labels": {"Code-Review": int(rate)}}
        self.rest.post('/changes/%s/revisions/%s/review' %
                       (change_id, revision_id), data=reviewInput)

    def setPlus2CodeReview(self, change_id, revision_id):
        self._submitCodeReview(change_id, revision_id, '+2')

    def setPlus1CodeReview(self, change_id, revision_id):
        self._submitCodeReview(change_id, revision_id, '+1')

    def setMinus2CodeReview(self, change_id, revision_id):
        self._submitCodeReview(change_id, revision_id, '-2')

    def setMinus1CodeReview(self, change_id, revision_id):
        self._submitCodeReview(change_id, revision_id, '-1')

    def setNoScoreCodeReview(self, change_id, revision_id):
        self._submitCodeReview(change_id, revision_id, '0')

    def _submitVerified(self, change_id, revision_id, rate):
        reviewInput = {"labels": {"Verified": int(rate)}}
        self.rest.post('/changes/%s/revisions/%s/review' %
                       (change_id, revision_id), data=reviewInput)

    def setPlus1Verified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '+1')

    def setMinus1Verified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '-1')

    def setNoScoreVerified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '0')


class RedmineUtil:
    def __init__(self, url, username=None, password=None, apiKey=None):
        if apiKey is not None:
            self.redmine = Redmine(url, key=apiKey)
        elif username is not None and password is not None:
            self.redmine = Redmine(url, username=username, password=password)
        else:
            self.redmine = Redmine(url)

    def isProjectExist(self, name):
        for p in self.redmine.projects:
            if p.name == name:
                return True
        return False

    def isIssueInProgress(self, issueId):
        return self.redmine.issues[issueId].status.id is 2

    def isIssueClosed(self, issueId):
        return self.redmine.issues[issueId].status.id is 5
