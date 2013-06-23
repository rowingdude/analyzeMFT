from distutils.core import setup

setup(
    name='analyzeMFT',
    version='2.0.4',
    author='David Kovar',
    author_email='dkovar@gmail.com',
    packages=['analyzemft','analyzemft.test'],
    url='http://github.com/dkovar/analyzeMFT',
    license='LICENSE.txt',
    description='Analyze the $MFT from a NTFS filesystem.',
    long_description=open('README.txt').read(),
    scripts=['analyzeMFT.py']
)

