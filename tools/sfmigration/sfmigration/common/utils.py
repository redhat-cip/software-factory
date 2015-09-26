#!/bin/env python
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import ConfigParser
import logging
from logging.handlers import RotatingFileHandler


def get_logger(logfile):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    log_format = '%(asctime)s :: %(levelname)s :: %(message)s'
    formatter = logging.Formatter(log_format)
    file_handler = RotatingFileHandler(logfile, 'a', 1000000, 1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARN)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


logger = get_logger('/tmp/sfmigration.log')


def get_config_value(config_file, section, option):
    cp = ConfigParser.ConfigParser()
    cp.read(config_file)
    try:
        return cp.get(section, option)
    except:
        return None


def get_mapping(config_file, original_value):
    new_value = get_config_value(config_file, 'MAPPINGS', original_value)
    if not new_value:
        logger.debug('no mapping found for %s' % original_value)
        new_value = original_value
    else:
        logger.debug('%s mapped to %s' % (original_value, new_value))
    return new_value


class BaseMapper(object):
    def map(self, x):
        return x


class ConfigMapper(BaseMapper):
    def __init__(self, config_file):
        self.config_file = config_file

    def map(self, x):
        return get_mapping(self.config_file, x)
