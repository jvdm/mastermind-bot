# mastermind-bot - A mastermind bot for slack
# © 2015 João Victor Duarte Martins <jvdm@sdf.org>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import sys

from setuptools import setup


def get_long_description(readme_path):
    from os import path
    from codecs import open

    here = path.abspath(path.dirname(__file__))
    readme_path = path.join(here, readme_path)
    with open(readme_path, encoding='utf-8') as readme:
        return readme.read()


def get_version(version_info_path):
    version_info = {}
    with open(version_info_path) as stream:
        exec(stream.read(), {}, version_info)
    return version_info['__version__']


setup(
    name='mastermind-bot',
    version=get_version('macacoprego/mastermind_bot/version_info.py'),
    description='A Mastermind bot for slack channels',
    long_description=get_long_description('README.rest'),
    url='https://github.com/macacoprego/mastermind-backend',
    author='João Victor Duarte Martins',
    author_email='jvdm@sdf.org',
    license='proprietary',
    packages=['macacoprego', 'macacoprego.mastermind_bot'],
    setup_requires=['wheel', 'isort'],
    install_requires=['aslack'],
    test_suite='eldiot.framework.test',
    tests_require=['fake-factory'],
    entry_points={
        'console_scripts': [
            'mastermind-bot = macacoprego.mastermind_bot:main']})
