"""
rjy -- A command-line tool for managing remote Jupyter sessions.

rjy is a command-line tool for managing remote Jupyter sessions
via SSH tunneling. This is only for Unix/Linux/OS X machines
currently, as it uses the ssh command line tool.

Because this relies on opening up SSH tunnels, use at
your own risk!
"""
from setuptools import setup

setup(
    name='remote_jupyter',
    version='0.1',
    license='BSD',
    long_description=__doc__,
    entry_points={
        'console_scripts': ['rjy=remote_jupyter:main']
    },
    dependencies=[
        "defopt",
        "tabulate"
    ]
)
