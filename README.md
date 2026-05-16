
# pyPreservica


[![Supported Versions](https://img.shields.io/pypi/pyversions/pyPreservica.svg)](https://pypi.org/project/pyPreservica)
[![CodeQL](https://github.com/carj/pyPreservica/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/carj/pyPreservica/actions/workflows/codeql-analysis.yml)
![PyPI Downloads](https://static.pepy.tech/badge/pypreservica)

Python language binding for the Preservica API

https://preservica.com/

This library provides a Python class for working with the Preservica Rest API

https://developers.preservica.com/api-reference

Wiki with example scripts https://github.com/carj/pyPreservica/wiki

## Quick Start

Set your credentials as environment variables:

```console
$ export PRESERVICA_USERNAME="user@example.com"
$ export PRESERVICA_PASSWORD="password"
$ export PRESERVICA_TENANT="PREVIEW"
$ export PRESERVICA_SERVER="preview.preservica.com"
```

Fetch an asset and browse its parent folder:

```python
from pyPreservica import *

client = EntityAPI()

# Fetch an asset by its UUID
asset = client.asset("dc949259-2c1d-4658-8eee-c17b27a8823d")
print(asset.title)         # LC-USZ62-20901
print(asset.security_tag)  # open

# List all children of a folder
folder = client.folder(asset.parent)
for child in client.children(folder.reference):
    print(child.title, child.entity_type)
```

Upload a file as a new asset into an existing folder:

```python
from pyPreservica import *

upload = UploadAPI()
folder_ref = "ae108c8f-b058-4228-b099-6049175d2f0c"
package = simple_asset_package(preservation_file="picture.tiff", parent_folder=folder_ref)
upload.upload_zip_package(package)
```

Search the repository:

```python
from pyPreservica import *

content = ContentAPI()
for hit in content.simple_search_csv("London"):
    print(hit)
```

Credentials can also be passed as constructor arguments or stored in a `credentials.properties` file.
See the [full documentation](https://pypreservica.readthedocs.io/) for all authentication options.

## Documentation

The full documentation is available at: https://pypreservica.readthedocs.io/

[![Documentation Status](https://readthedocs.org/projects/pypreservica/badge/?version=latest)](https://pypreservica.readthedocs.io/en/latest/?badge=latest)

## Contributing

Bug reports and pull requests are welcome on GitHub at https://github.com/carj/pyPreservica

For announcements about new versions and discussion of pyPreservica please subscribe to the google groups
forum https://groups.google.com/g/pypreservica

## License

The package is available as open source under the terms of the Apache License 2.0


## Installation

pyPreservica is available from the Python Package Index (PyPI)

https://pypi.org/project/pyPreservica/

To install pyPreservica, simply run this simple command in your terminal of choice:


    $ pip install pyPreservica

