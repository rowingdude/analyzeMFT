import setuptools
from distutils.core import setup

setup(
    name='analyzeMFT',
    version='3.0.1',
    author='Benjamin Cance',
    author_email='bjc@tdx.li',
    packages=['analyzemft'],
    url='http://github.com/rowingdude/analyzeMFT',
    license='LICENSE.txt',
    description='Analyze the $MFT from a NTFS filesystem.',
    long_description=open('README.txt').read(),
    scripts=['analyzeMFT.py']
)
