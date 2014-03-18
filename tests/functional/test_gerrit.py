#!/usr/bin/python

from utils import Base

class GerritFunctionalTests(Base):
    def test_02_delete_repository(self):
        print "Delete repository"
        print "Check if it is deleted"
    def test_01_create_repository(self):
        print "Create repository"
        print "Check if it is clonable"

