#!/usr/bin/env python

from distutils.core import setup, Extension

uinput = Extension('libuinput',
                   sources = ['src/uinput.c'])

setup(name='python-steamcontroller',
      version='1.0',
      description='Steam Controller userland driver',
      author='Stany MARCEL',
      author_email='stanypub@gmail.com',
      url='https://github.com/ynsta/steamcontroller',
      package_dir={'steamcontroller': 'src'},
      packages=['steamcontroller'],
      scripts=['scripts/sc-dump.py',
               'scripts/sc-xbox.py'],
      license='MIT',
      platforms=['Linux'],
      ext_modules=[uinput, ])
