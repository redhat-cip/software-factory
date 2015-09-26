#!/bin/env python


class BaseEncoder:
    def __init__(self, encoder_type):
        self.encoder_type = encoder_type

    def encode(self, data):
        return data

    def decode(self, data):
        return data
