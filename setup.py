from distutils import setup

setup(
    name='analyzeMFT',
    version='2.1.1',
    author='Benjamin Cance',
    author_email='bjc@tdx.li',
    packages=['analyzemft'],
    url='http://github.com/rowingdude/analyzeMFT',
    license='LICENSE.txt',
    description='Analyze the $MFT from a NTFS filesystem.',
    long_description=open('README.txt').read(),
    scripts=['analyzeMFT.py']
)
