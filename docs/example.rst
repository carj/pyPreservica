Example Applications
~~~~~~~~~~~~~~~~~~~~~~

**Updating a descriptive metadata element value**

If you need to bulk update metadata values the following script will check every asset in a folder given by the "folder-uuid"
and find the matching descriptive metadata document by its namespace "your-xml-namespace".
It will then find a particular element in the xml document "your-element-name" and update its value. ::

    from xml.etree import ElementTree
    from pyPreservica import *
    client = EntityAPI()
    folder = client.folder("folder-uuid")
    next_page = None
    while True:
        children = client.children(folder.reference, maximum=10, next_page=next_page)
        for entity in children.results:
            if entity.entity_type is EntityAPI.EntityType.ASSET:
                asset = client.asset(entity.reference)
                for url, schema in asset.metadata.items():
                    if schema == "your-xml-namespace":
                        xml_document = ElementTree.fromstring(client.metadata(url))
                        field_with_error = xml_document.find('.//{your-xml-namespace}your-element-name')
                        if hasattr(field_with_error, 'text'):
                            if field_with_error.text == "Old Value":
                                field_with_error.text = "New Value"
                                asset = client.update_metadata(asset, schema, ElementTree.tostring(xml_document, encoding='UTF-8', xml_declaration=True).decode("utf-8"))
                                print("Updated asset: " + asset.title)
        if not children.has_more:
            break
        else:
            next_page = children.next_page


The following script does the same thing as above but uses the function descendants() rather than children().
The difference is that descendants() does the paging of results internally and combined with
a filter() on the lazy iterator provides a version which does not need the additional while loop or if statement! ::

    client = EntityAPI()
    folder = client.folder("folder-uuid")
    for child_asset in filter(only_assets, client.descendants(folder.reference)):
        asset = client.asset(child_asset.reference)
        document = ElementTree.fromstring(client.metadata_for_entity(asset, "your-xml-namespace"))
        field_with_error = document.find('.//{your-xml-namespace}your-element-name')
        if hasattr(field_with_error, 'text'):
            if field_with_error.text == "Old Value":
                field_with_error.text = "New Value"
                new_xml = ElementTree.tostring(document, encoding='UTF-8', xml_declaration=True).decode("utf-8")
                asset = client.update_metadata(asset, "your-xml-namespace", new_xml)
                print("Updated asset: " + asset.title)

**Adding Metadata from a Spreadsheet**

One common use case which can be solved with pyPreservica is adding descriptive metadata to existing Preservica assets or folders
using metadata held in a spreadsheet. Normally each column in the spreadsheet contains a metadata attribute and each row represents a
different asset.

The following is a short python script which uses pyPreservica to update assets within Preservica
with Dublin Core Metadata held in a spreadsheet.

The spreadsheet should contain a header row. The column name in the header row
should start with the text "dc:" to be included.
There should be one column called "assetId" which contains the reference id for the asset to be updated.

The metadata should be saved as a UTF-8 CSV file called dublincore.csv ::

    import xml
    import csv
    from pyPreservica import *

    OAI_DC = "http://www.openarchives.org/OAI/2.0/oai_dc/"
    DC = "http://purl.org/dc/elements/1.1/"
    XSI = "http://www.w3.org/2001/XMLSchema-instance"

    entity = EntityAPI()

    headers = list()
    with open('dublincore.csv', encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for header in row:
                headers.append(header)
            break
        if 'assetId' in headers:
            for row in reader:
                assetID = None
                xml_object = xml.etree.ElementTree.Element('oai_dc:dc', {"xmlns:oai_dc": OAI_DC, "xmlns:dc": DC, "xmlns:xsi": XSI})
                for value, header in zip(row, headers):
                    if header.startswith('dc:'):
                        xml.etree.ElementTree.SubElement(xml_object, header).text = value
                    elif header.startswith('assetId'):
                        assetID = value
                xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8', xml_declaration=True).decode('utf-8')
                asset = entity.asset(assetID)
                entity.add_metadata(asset, OAI_DC, xml_request)
        else:
            print("The CSV file should contain a assetId column containing the Preservica identifier for the asset to be updated")



**Creating Searchable Transcripts from Oral Histories**

The following is an example python script which uses a 3rd party Machine Learning API to automatically generate a text
transcript from an audio file such as a WAVE file.
The transcript is then uploaded to Preservica, is stored as metadata attached to an asset and indexed so that the audio or oral history is searchable.

This example uses the AWS https://aws.amazon.com/transcribe/ service, but other AI APIs are also available.
AWS provides a free tier https://aws.amazon.com/free/ to allow you to try the service for no cost.

This python script does require a set of AWS credentials to use the AWS transcribe service.

The python script downloads a WAV file using its reference, uploads it to AWS S3 and then starts the transcription service,
when the transcript is available it creates a metadata document containing the text and uploads it to Preservica.::

    import os,time,uuid,xml,boto3,requests
    from pyPreservica import *

    BUCKET = "com.my.transcribe.bucket"
    AWS_KEY = '.....'
    AWS_SECRET = '........'
    REGION = 'eu-west-1'
    ## download the file to the local machine
    client = EntityAPI()
    asset = client.asset('91c73c95-a298-448c-a5a3-2295e5052be3')
    client.download(asset, f"{asset.reference}.wav")
    # upload the file to AWS
    s3_client = boto3.client('s3', region_name=REGION, aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET)
    response = s3_client.upload_file(f"{asset.reference}.wav", BUCKET, f"{asset.reference}")
    # Start the transcription service
    transcribe = boto3.client('transcribe', region_name=REGION, aws_access_key_id=KEY, aws_secret_access_key=SECRET)
    job_name = str(uuid.uuid4())
    job_uri = f"https://s3-{REGION}.amazonaws.com/{BUCKET}/{asset.reference}"
    transcribe.start_transcription_job(TranscriptionJobName=job_name,  Media={'MediaFileUri': job_uri}, MediaFormat='wav', LanguageCode='en-US')
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        print("Still working on the transcription....")
        time.sleep(5)
    # upload the transcript text to Preservica
    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        result_url = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        json = requests.get(result_url).json()
        text = json['results']['transcripts'][0]['transcript']
        xml_object = xml.etree.ElementTree.Element('tns:Transcript', {"xmlns:tns": "https://aws.amazon.com/transcribe/"})
        xml.etree.ElementTree.SubElement(xml_object, "Transcription").text = text
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8', xml_declaration=True).decode('utf-8')
        client.add_metadata(asset, "https://aws.amazon.com/transcribe/", xml_request)   # add the xml transcript
        s3_client.delete_object(Bucket=BUCKET, Key=asset.reference)   # delete the temp file from s3
        os.remove(f"{asset.reference}.wav")    # delete the local copy


