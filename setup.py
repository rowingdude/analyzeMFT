from setuptools import setup, find_packages
from src.analyzeMFT.constants import VERSION

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='analyzeMFT',
    version=VERSION,
    author='Benjamin Cance',
    author_email='bjc@tdx.li',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    url='http://github.com/rowingdude/analyzeMFT',
    license='LICENSE.txt',
    description='Analyze the $MFT from a NTFS filesystem.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    scripts=['analyzeMFT.py'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pywin32;platform_system=='Windows'",
    ],
    entry_points={
        'console_scripts': [
            'analyzemft=analyzeMFT:main',
        ],
    },
)