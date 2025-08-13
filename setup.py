from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='analyzeMFT',
    version='3.1.0',
    author='Benjamin Cance',
    author_email='kc8bws@kc8bws.com',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    package_data={
        'analyzeMFT': ['sql/*.sql'],
    },
    url='http://github.com/rowingdude/analyzeMFT',
    license='LICENSE.txt',
    description='Analyze the $MFT from a NTFS filesystem.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pywin32;platform_system=='Windows'",
        "openpyxl==3.1.5",
    ],
    entry_points={
        'console_scripts': [
            'analyzemft=analyzeMFT:main',
        ],
    },
)