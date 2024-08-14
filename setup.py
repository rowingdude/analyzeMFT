from setuptools import setup, find_packages

with open('README.txt', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='analyzeMFT',
    version='2.1.1',
    author='Benjamin Cance',
    author_email='bjc@tdx.li',
    packages=find_packages(),
    url='http://github.com/rowingdude/analyzeMFT',
    license='LICENSE.txt',
    description='Analyze the $MFT from a NTFS filesystem.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    scripts=['analyzeMFT.py'],
    install_requires=[
        'typing;python_version<"3.5"',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: System :: Filesystems',
        'Topic :: Utilities',
    ],
    python_requires='>=3.6',
)