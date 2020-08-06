from setuptools import setup, find_packages


setup(
    name='pytradelib',
    version='0.0.1',
    license='Apache-2.0',
    author='Brian Cappello',
    author_email='briancappello@gmail.com',
    install_requires=[
        'aiohttp',
        'pandas',
        'pytz',
        'requests',
        'scipy',
        'ta-lib',
    ],
    packages=find_packages(exclude=['docs', 'test']),
    include_package_data=True,
    zip_safe=False,
)
