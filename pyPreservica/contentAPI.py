import requests

from pyPreservica.common import AuthenticatedAPI, Thumbnail, CHUNK_SIZE, EntityType


class ContentAPI(AuthenticatedAPI):
    """
         A client library for the Preservica Repository web services Content API
         https://us.preservica.com/api/content/documentation.html

    """

    def object_details(self, entity_type, reference):
        headers = {'Preservica-Access-Token': self.token}
        if entity_type == EntityType.ASSET:
            params = {'id': f'sdb:IO|{reference}'}
        elif entity_type == EntityType.FOLDER:
            params = {'id': f'sdb:SO|{reference}'}
        else:
            print(f"entity_type must be a folder or asset")
            raise SystemExit
        request = requests.get(f'https://{self.server}/api/content/object-details', params=params, headers=headers)
        if request.status_code == requests.codes.ok:
            return request.json()["value"]
        elif request.status_code == requests.codes.not_found:
            raise RuntimeError(reference, "The requested reference is not found in the repository")
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.indexed_fields()
        else:
            print(f"object_details failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def download(self, entity_type, reference, filename):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/octet-stream'}
        if entity_type == "IO":
            params = {'id': f'sdb:IO|{reference}'}
        elif entity_type == "SO":
            params = {'id': f'sdb:SO|{reference}'}
        else:
            print(f"entity must be a folder or asset")
            raise SystemExit
        with requests.get(f'https://{self.server}/api/content/download', params=params, headers=headers, stream=True) as req:
            if req.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                        file.flush()
                file.close()
                return filename
            elif req.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.download(entity_type, reference, filename)
            elif req.status_code == requests.codes.not_found:
                raise RuntimeError(reference, "The requested reference is not found in the repository")
            else:
                print(f"download failed with error code: {req.status_code}")
                print(req.request.url)
                raise SystemExit

    def thumbnail(self, entity_type, reference, filename, size=Thumbnail.LARGE):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/octet-stream'}
        if entity_type == "IO":
            params = {'id': f'sdb:IO|{reference}', 'size': f'{size.value}'}
        elif entity_type == "SO":
            params = {'id': f'sdb:SO|{reference}', 'size': f'{size.value}'}
        else:
            print(f"entity must be a folder or asset")
            raise SystemExit
        with requests.get(f'https://{self.server}/api/content/thumbnail', params=params, headers=headers) as req:
            if req.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                        file.flush()
                file.close()
                return filename
            elif req.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.thumbnail(entity_type, reference, filename, size)
            elif req.status_code == requests.codes.not_found:
                raise RuntimeError(reference, "The requested reference is not found in the repository")
            else:
                print(f"thumbnail failed with error code: {req.status_code}")
                print(req.request.url)
                raise SystemExit

    def indexed_fields(self):
        headers = {'Preservica-Access-Token': self.token}
        results = requests.get(f'https://{self.server}/api/content/indexed-fields', headers=headers)
        if results.status_code == requests.codes.ok:
            fields = list()
            for ob in results.json()["value"]:
                field = f'{ob["shortName"]}.{ob["index"]}'
                fields.append(field)
            return fields
        elif results.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.indexed_fields()
        else:
            print(f"indexed_fields failed with error code: {results.status_code}")
            print(results.request.url)
            raise SystemExit

    def simple_search(self, query, start_index=0, page_size=10, *args):
        start_from = str(start_index)
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Preservica-Access-Token': self.token}
        queryterm = ('{ "q":  "%s" }' % query)
        metadata_fields = ','.join(*args)
        payload = {'start': start_from, 'max': str(page_size), 'metadata': metadata_fields, 'q': queryterm}
        results = requests.post(f'https://{self.server}/api/content/search', data=payload, headers=headers)
        results_list = list()
        if results.status_code == requests.codes.ok:
            json = results.json()
            metadata = json['value']['metadata']
            refs = list(json['value']['objectIds'])
            hits = int(json['value']['totalHits'])
            for row in metadata:
                results_map = dict()
                for li in row:
                    results_map[li['name']] = li['value']
                results_list.append(results_map)
            next_start = start_index + page_size
            cls = type('SearchResult', (object,), {'metadata': metadata, 'refs': refs, 'hits': hits, 'results_list': results_list, 'next_start': next_start})
            return cls
        elif results.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.simple_search(query, start_index, page_size, *args)
        else:
            print(f"search failed with error code: {results.status_code}")
            print(results.request.url)
            raise SystemExit
