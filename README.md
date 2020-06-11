# pyPreservica
Python language binding for the Preservica API

This library provides a Python class for working with the Preservica Entity Rest API

https://us.preservica.com/api/entity/documentation.html

The library includes the following calls:

* asset() Fetches the main attributes for an asset by its reference.
* folder() Fetches the main attributes for a folder by its reference.
* metadata() Return the descriptive metadata attached to an entity.
* save() Updates the title and description of an asset or folder.
* create_folder() Creates a new structural object in the repository.
* children() Returns a list of child entities from a folder.
* identifier() Returns an asset or folder based on an external identifier.
* add_identifier() Adds a new external identifier to an entity.
* add_metadata() Add new descriptive metadata to an entity.
* update_metadata() Update the descriptive metadata attached to an entity.

## usage 
````
from pyPreservica.entityAPI import EntityAPI

client = EntityAPI(username="test@test.com", password="123444", tenant="PREVIEW", server="preview.preservica.com")

asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
asset.title = "New Asset Title"
asset.description = "New Asset Description"
asset = client.save(asset)



````