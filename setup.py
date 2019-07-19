import setuptools
from distutils.core import setup

setup(
    name='analyzeMFT3',
    version='3.0.0',
    author='David Kovar',
    author_email='dkovar@gmail.com',
    packages=['analyzemft'],
    url='http://github.com/eddsalkield/analyzeMFT3',
    license='LICENSE.txt',
    description='Analyze the $MFT from a NTFS filesystem.',
    long_description=open('README.txt').read(),
    scripts=['analyzeMFT.py']
)
