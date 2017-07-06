from setuptools import setup, find_packages

setup(
    name='pomu',
    version='0.1',
    description='A utility to manage portage overlays',
    url='https://gentoo.org',
    author='Mykyta Holubakha',
    author_email='hilobakho@gmail.com',
    license='GNU GPLv2',
    packages=find_packages(exclude=['tests']),
    install_requires=['Click', 'GitPython', 'patch'],
    entry_points={
        'console_scripts':['pomu = pomu.cli:main_']
    }
)
