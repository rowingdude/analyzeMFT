from distutils.core import setup

setup(
    name='analyzeMFT',
    version='2.0.15',
    author='David Kovar',
    author_email='dkovar@gmail.com',
    packages=['analyzemft'],
    url='http://github.com/dkovar/analyzeMFT',
    license='LICENSE.txt',
    description='Analyze the $MFT from a NTFS filesystem.',
    long_description=open('README.txt').read(),
    scripts=['analyzeMFT.py']
)

