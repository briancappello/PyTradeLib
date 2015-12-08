import os
from setuptools import setup, find_packages

NAME = 'pytradelib'


def readme():
    with open('README.md') as f:
        return f.read()

INSTALL_REQUIRES = ([
    'pandas',
    'requests',
    'grequests==0.3.0',
    'pytz',
    'ta-lib',
])

DEPENDENCY_LINKS = [
    'https://github.com/briancappello/grequests/tarball/master#egg=grequests-0.3.0',
]

setup(
    name=NAME,
    version='0.0.1',
    license='BSD License',
    author='Brian Cappello',
    author_email='briancappello@gmail.com',
    install_requires=INSTALL_REQUIRES,
    dependency_links=DEPENDENCY_LINKS,
    packages=find_packages('.'),
    zip_safe=False,
)
