import setuptools
from distutils.core import setup

setup(
    name='analyzeMFT',
    version='3.0.1',
    author='David Kovar',
    author_email='dkovar@gmail.com',
    packages=['analyzemft'],
    url='http://github.com/dkovar/analyzeMFT',
    license='LICENSE.txt',
    description='Analyze the $MFT from a NTFS filesystem.',
    long_description=open('README.txt').read(),
    scripts=['analyzeMFT.py']
)
