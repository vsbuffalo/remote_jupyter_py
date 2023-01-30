from setuptools import setup

setup(
    name='remote_jupyter',
    version='0.1dev',
    packages=['rjy',],
    license='BSD',
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': ['src=main:cli']
    }
)
