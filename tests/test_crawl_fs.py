import pytest
from pyPreservica import *


def test_crawl_fs():
    path = "./test_data/"
    bucket = "com.preservica.dev.preview.sales.autoupload"

    client = UploadAPI()
    entity = EntityAPI()

    parent = entity.folder("daa88307-4a0b-4962-a5a9-6a1387f9f876")

    for e in entity.all_descendants(parent):
        if e.entity_type == EntityType.ASSET:
            entity.delete_asset(e, "delete", "delete")
        else:
            entity.delete_folder(e, "delete", "delete")

    client.crawl_filesystem(filesystem_path=path, bucket_name=bucket,
                            preservica_parent="daa88307-4a0b-4962-a5a9-6a1387f9f876")






