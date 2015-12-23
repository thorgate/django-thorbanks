#!/usr/bin/env python

import os
import sys

from setuptools import setup, find_packages

from thorbanks import __version__ as version


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    readme = f.read()


setup(
    name='django-thorbanks',
    version=version,
    description='`django-thorbanks` provides a Django application for Estonian banklinks.',
    long_description=readme,
    author="Thorgate",
    author_email='info@thorgate.eu',
    url='http://thorgate.eu',
    packages=find_packages(),
    package_data={'thorbanks': [
        'static/img/payment/*',
        'templates/thorbanks/*',
    ]},
    include_package_data=True,
    install_requires=[
        'Django>=1.4,<1.10',
        'PyCrypto',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
