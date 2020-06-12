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
* download() Download the latest generation of the preservation representation.
* thumbnail() Download the thumbnail icon for an asset or folder.

## usage 
````

from pyPreservica.entityAPI import EntityAPI,Thumbnail

client = EntityAPI(username="test@test.com", password="123444", tenant="PREVIEW", server="preview.preservica.com")

asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
asset.title = "New Asset Title"
asset.description = "New Asset Description"
asset = client.save(asset)

folder = client.create_folder("title", "description", "open", "249c989a-84b2-467a-819a-941d8bee4976")

asset = entity.asset("9bad5acf-e7ce-458a-927d-2d1e7f15974d")
client.add_identifier(asset, "ISBN", "978-3-16-148410-0")
client.add_identifier(asset, "DOI", "https://doi.org/10.1109/5.771073")
client.add_identifier(asset, "URN", "urn:isan:0000-0000-2CEA-0000-1-0000-0000-Y")

for e in client.identifier("ISBN", "978-3-16-148410-0"):
      print(e.type, e.reference, e.title)

with open("DublinCore.xml", 'r', encoding="UTF-8") as md:
      asset = client.add_metadata(asset, "http://purl.org/dc/elements/1.1/", md)

file = open("thumbnail.jpg", "wb")
file.write(client.thumbnail(asset, Thumbnail.LARGE))
file.close()

file = open("picture.jpg", "wb")
file.write(client.download(asset))
file.close()

````