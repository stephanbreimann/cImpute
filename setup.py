#!/usr/bin/env python

from setuptools import setup

setup(
    name="cImpute",
    version='1.0',
    description='conditional imputation for omics data',
    author='Stephan Breimann',
    author_email='stephanbreimann@yahoo.de',
    url=None,
    packages=['c_impute'],
    include_package_data=True,
    package_data={"": ["*.xlsx"]}
)
