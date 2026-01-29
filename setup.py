import pathlib
import sys
import os
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

PKG = "pyPreservica"

# 'setup.py publish' shortcut.
if sys.argv[-1] == 'publish':
    os.system('python -m build')
    os.system('twine upload dist/*')
    sys.exit()


# This call to setup() does all the work
setup(
    name=PKG,
    version="3.4.1",
    description="Python library for the Preservica API",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://pypreservica.readthedocs.io/",
    author="James Carr",
    author_email="drjamescarr@gmail.com",
    license="Apache License 2.0",
    packages=["pyPreservica"],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        "Operating System :: OS Independent",
        "Topic :: System :: Archiving",
    ],
    keywords='Preservica API Preservation',
    install_requires=["requests", "urllib3", "certifi", "boto3>=1.38.0", "botocore>=1.38.0", "s3transfer", "azure-storage-blob", "tqdm", "pyotp", "python-dateutil"],
    project_urls={
        'Documentation': 'https://pypreservica.readthedocs.io',
        'Source': 'https://github.com/carj/pyPreservica',
        'Discussion Forum': 'https://groups.google.com/g/pypreservica',
    }
)
