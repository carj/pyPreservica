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
* representations()  Return a list of all the representations of an asset.
* content_objects()  Return a list of all the content objects within a representation.
* generations()  Return a list of all the generations of a content object
* bitstream_content() Download a bytestream to a local file


## usage 
````

from pyPreservica.entityAPI import EntityAPI,Thumbnail

client = EntityAPI(username="test@test.com", password="123444", tenant="PREVIEW", server="preview.preservica.com")

asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
asset.title = "New Asset Title"
asset.description = "New Asset Description"
asset = client.save(asset)

folder = client.folder("0b0f0303-6053-4d4e-a638-4f6b81768264")
folder.title = "New Folder Title"
folder.description = "New Folder Description"
folder = client.save(folder)

client.add_identifier(folder, "ISBN", "122333333")

folder = client.create_folder("title", "description", "open", "249c989a-84b2-467a-819a-941d8bee4976")

asset = client.asset("9bad5acf-e7ce-458a-927d-2d1e7f15974d")
client.add_identifier(asset, "ISBN", "978-3-16-148410-0")
client.add_identifier(asset, "DOI", "https://doi.org/10.1109/5.771073")
client.add_identifier(asset, "URN", "urn:isan:0000-0000-2CEA-0000-1-0000-0000-Y")

for e in client.identifier("ISBN", "978-3-16-148410-0"):
      print(e.type, e.reference, e.title)

with open("DublinCore.xml", 'r', encoding="UTF-8") as md:
      asset = client.add_metadata(asset, "http://purl.org/dc/elements/1.1/", md)

client.download(asset, "picture.jpg"))
client.thumbnail(asset, "thumbnail.jpg", Thumbnail.LARGE)

representations = client.representations(asset):
for representation in representations:
    print(representation.type)
    print(representation.name)
    for content_object in client.content_objects(r):
        print(content_object.title)
        print(content_object.description)
        for generation in client.generations(content_object):
            print(generation.original)
            print(generation.active)
            print(generation.format_group)
            print(generation.effective_date)
            for bitstream in generation.bitstreams:
                print(bitstream.filename)
                print(bitstream.length)
                print(bitstream.fixity.items())
                client.bitstream_content(bitstream, bitstream.filename)
            

````