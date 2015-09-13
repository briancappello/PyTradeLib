import os
from setuptools import setup

NAME = 'pytradelib'

def readme():
    with open('README.md') as f:
        return f.read()

INSTALL_REQUIRES = ([
    'pandas',
    'pandas-datareader',
    'tables',
    'requests',
    'grequests',
    'pytz',
])

setup(
    name=NAME,
    version='0.0.1',
    license='BSD License',
    author='Brian Cappello',
    author_email='briancappello@gmail.com',
    install_requires=INSTALL_REQUIRES,
    packages=['pytradelib'],
    zip_safe=False,
)
