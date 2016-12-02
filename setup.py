#!/usr/bin/env python

import sys
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

uinput = Extension('libuinput',
                   sources = ['src/uinput.c'])

deps = ['libusb1', 'psutil']
if sys.version_info < (3,4):
    deps.append('enum34')

setup(name='python-steamcontroller',
      version='1.2',
      description='Steam Controller userland driver',
      author='Stany MARCEL',
      author_email='stanypub@gmail.com',
      url='https://github.com/ynsta/steamcontroller',
      package_dir={'steamcontroller': 'src'},
      packages=['steamcontroller'],
      scripts=['scripts/sc-dump.py',
               'scripts/sc-xbox.py',
               'scripts/sc-desktop.py',
               'scripts/sc-mixed.py',
               'scripts/sc-test-cmsg.py',
               'scripts/sc-gyro-plot.py',
               'scripts/vdf2json.py',
               'scripts/json2vdf.py'],
      license='MIT',
      platforms=['Linux'],
      install_requires=deps,
      ext_modules=[uinput, ])
