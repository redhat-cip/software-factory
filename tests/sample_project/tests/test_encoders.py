#!/bin/env python

import unittest

from sample.encoder import BaseEncoder

DATA = "test_data"


class TestsEncoderBasic(unittest.TestCase):
    def test_encode(self):
        result = BaseEncoder("void").encode(DATA)
        self.assertEquals(result, DATA)

    def test_decode(self):
        result = BaseEncoder("void").decode(DATA)
        self.assertEquals(result, DATA)
