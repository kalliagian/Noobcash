from setuptools import setup

setup(
    name='cli',
    version='1.0',
    py_modules = ['noobcash'],
    install_requires=[
            'Click', 'Requests', 'colorama',
    ],
    entry_points={
            'console_scripts': ['noobcash=noobcash:cli']
    },
)
