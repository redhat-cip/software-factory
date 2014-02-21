#!/usr/bin/env python

from setuptools import setup

setup(name='managesf',
      version='0.1',
      description='Management of a deployed SF',
      author='eNovance',
      author_email='devs@enovance.com',
      scripts=['manage'],
      url='',
      install_requires=['dulwich', 'pyredmine', 'gerritlib',
                        'python-dateutil', 'pyaml'],
      packages=['managesf'],
     )
