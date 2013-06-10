from distutils.core import setup

setup(
    name='analyzeMFT',
    version='2.0.0',
    author='David Kovar',
    author_email='dkovar@gmail.com',
    packages=['analyzemft','analyzemft.test'],
#    scripts=['bin/stowe-towels.py','bin/wash-towels.py'],
    url='http://github.com/dkovar/analyzeMFT',
    license='LICENSE.txt',
    description='Analyze the $MFT from a NTFS filesystem.',
    long_description=open('README.txt').read(),
    install_requires=[],
)

