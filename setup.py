#!/usr/bin/env python

from setuptools import setup


if __name__ == '__main__':
    extra_requires = {}

    all_packages = []
    for values in extra_requires.values():
        all_packages.extend(values)
    extra_requires['all'] = all_packages

    setup(
        name='tide',
        version='0.0.0',
        description='Tree Integrated Development Environment',
        author='Pierre Delaunay',
        extras_require=extra_requires,
        packages=[
            'tide',
            'tide.ide',
            'tide.generators',
        ],
        setup_requires=['setuptools'],
        install_require=['PySDL2'],
        tests_require=['pytest', 'flake8', 'codecov', 'pytest-cov'],
        entry_points={
            'console_scripts': [
            ]
        }
    )
