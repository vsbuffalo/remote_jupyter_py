from setuptools import setup

setup(
    name='remote_jupyter',
    version='0.1dev',
    license='BSD',
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': ['rjy=remote_jupyter:main']
    },
    dependencies=[
        "defopt",
        "tomllib"
    ]
)
