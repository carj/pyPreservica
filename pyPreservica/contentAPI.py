import requests
import csv

from pyPreservica.common import AuthenticatedAPI, Thumbnail, CHUNK_SIZE, HEADER_TOKEN, content_api_identifier_to_type


class ContentAPI(AuthenticatedAPI):
    """
         A client library for the Preservica Repository web services Content API
         https://us.preservica.com/api/content/documentation.html

    """

    def __init__(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False):
        super().__init__(username, password, tenant, server, use_shared_secret)
        self.callback = None

    class SearchResult:
        def __init__(self, metadata, refs, hits, results_list, next_start):
            self.metadata = metadata
            self.refs = refs
            self.hits = int(hits)
            self.results_list = results_list
            self.next_start = next_start

    def search_callback(self, fn):
        self.callback = fn

    def object_details(self, entity_type, reference):
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json'}
        params = {'id': f'sdb:{entity_type.value}|{reference}'}
        request = requests.get(f'https://{self.server}/api/content/object-details', params=params, headers=headers)
        if request.status_code == requests.codes.ok:
            return request.json()["value"]
        elif request.status_code == requests.codes.not_found:
            raise RuntimeError(reference, "The requested reference is not found in the repository")
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.object_details(entity_type, reference)
        else:
            print(f"object_details failed with error code: {request.status_code}")
            print(request.request.url)
            raise RuntimeError(request.status_code, f"object_details failed with error code: {request.status_code}")

    def download(self, reference, filename):
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream'}
        params = {'id': f'sdb:IO|{reference}'}
        with requests.get(f'https://{self.server}/api/content/download', params=params, headers=headers,
                          stream=True) as req:
            if req.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                        file.flush()
                file.close()
                return filename
            elif req.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.download(reference, filename)
            elif req.status_code == requests.codes.not_found:
                raise RuntimeError(reference, "The requested reference is not found in the repository")
            else:
                print(f"download failed with error code: {req.status_code}")
                print(req.request.url)
                raise RuntimeError(req.status_code, f"download failed with error code: {req.status_code}")

    def thumbnail(self, entity_type, reference, filename, size=Thumbnail.LARGE):
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream'}
        if entity_type == "IO":
            params = {'id': f'sdb:IO|{reference}', 'size': f'{size.value}'}
        elif entity_type == "SO":
            params = {'id': f'sdb:SO|{reference}', 'size': f'{size.value}'}
        else:
            print(f"entity_type must be a folder or asset, IO or SO")
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
                raise RuntimeError(req.status_code, f"thumbnail failed with error code: {req.status_code}")

    def indexed_fields(self):
        headers = {HEADER_TOKEN: self.token}
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
            raise RuntimeError(results.status_code, f"indexed_fields failed with error code: {results.status_code}")

    def simple_search_csv(self, query: str = "%", csv_file="search.csv", *args):
        page_size = 50
        if len(args) == 0:
            metadata_fields = ["xip.reference", "xip.title", "xip.description", "xip.document_type",
                               "xip.parent_ref", "xip.security_descriptor"]
        else:
            metadata_fields = list(*args)
        if "xip.reference" not in metadata_fields:
            metadata_fields.insert(0, "xip.reference")
        with open(csv_file, newline='', mode="wt", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=metadata_fields)
            writer.writeheader()
            writer.writerows(self.simple_search_list(query, page_size, *args))

    def simple_search_list(self, query: str = "%", page_size: int = 10, *args):
        search_result = self.simple_search(query, 0, page_size, *args)
        for e in search_result.results_list:
            yield e
        found = len(search_result.results_list)
        while search_result.hits > found:
            search_result = self.simple_search(query, found, page_size, *args)
            for e in search_result.results_list:
                yield e
            found = found + len(search_result.results_list)

    def simple_search(self, query: str = "%", start_index: int = 0, page_size: int = 10, *args):
        start_from = str(start_index)
        headers = {'Content-Type': 'application/x-www-form-urlencoded', HEADER_TOKEN: self.token}
        queryterm = ('{ "q":  "%s" }' % query)
        if len(args) == 0:
            metadata_fields = "xip.title,xip.description,xip.document_type,xip.parent_ref,xip.security_descriptor"
        else:
            metadata_fields = ','.join(*args)
        payload = {'start': start_from, 'max': str(page_size), 'metadata': metadata_fields,
                   'q': queryterm}
        results = requests.post(f'https://{self.server}/api/content/search', data=payload,
                                headers=headers)
        results_list = list()
        if results.status_code == requests.codes.ok:
            json = results.json()
            metadata = json['value']['metadata']
            refs = list(json['value']['objectIds'])
            refs = list(map(lambda x: content_api_identifier_to_type(x), refs))
            hits = int(json['value']['totalHits'])

            for m_row, r_row in zip(metadata, refs):
                results_map = dict()
                results_map['xip.reference'] = r_row[1]
                for li in m_row:
                    results_map[li['name']] = li['value']
                results_list.append(results_map)
            next_start = start_index + page_size

            if self.callback is not None:
                value = str(f'{len(results_list) + start_index}:{hits}')
                self.callback(value)

            search_results = self.SearchResult(metadata, refs, hits, results_list, next_start)
            return search_results
        elif results.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.simple_search(query, start_index, page_size, *args)
        else:
            print(f"search failed with error code: {results.status_code}")
            print(results.request.url)
            raise RuntimeError(results.status_code, f"simple_search failed with error code: {results.status_code}")

    def search_index_filter_csv(self, query: str = "%", csv_file="search.csv", map_fields=None):
        page_size = 50
        if map_fields is None:
            map_fields = dict()
        if "xip.reference" not in map_fields:
            map_fields["xip.reference"] = ""

        header_fields = list(map_fields.keys())
        index = header_fields.index("xip.reference")
        header_fields.insert(0, header_fields.pop(index))
        with open(csv_file, newline='', mode="wt", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header_fields)
            writer.writeheader()
            writer.writerows(self.search_index_filter_list(query, page_size, map_fields))

    def search_index_filter_list(self, query: str = "%", page_size: int = 10, map_fields=None):
        search_result = self.search_index_filter(query, 0, page_size, map_fields)
        for e in search_result.results_list:
            yield e
        found = len(search_result.results_list)
        while search_result.hits > found:
            search_result = self.search_index_filter(query, found, page_size, map_fields)
            for e in search_result.results_list:
                yield e
            found = found + len(search_result.results_list)

    def search_index_filter(self, query: str = "%", start_index: int = 0, page_size: int = 10, map_fields=None):
        start_from = str(start_index)
        headers = {'Content-Type': 'application/x-www-form-urlencoded', HEADER_TOKEN: self.token}

        field_list = list()
        for key, value in map_fields.items():
            if value == "":
                field_list.append('{' f' "name": "{key}", "values": [] ' + '}')
            else:
                field_list.append('{' f' "name": "{key}", "values": ["{value}"] ' + '}')

        filter_terms = ','.join(field_list)

        queryterm = ('{ "q":  "%s",  "fields":  [ %s ] }' % (query, filter_terms))

        payload = {'start': start_from, 'max': str(page_size), 'metadata': list(map_fields.keys()), 'q': queryterm}
        results = requests.post(f'https://{self.server}/api/content/search', data=payload, headers=headers)
        results_list = list()
        if results.status_code == requests.codes.ok:
            json = results.json()
            metadata = json['value']['metadata']
            refs = list(json['value']['objectIds'])
            refs = list(map(lambda x: content_api_identifier_to_type(x), refs))
            hits = int(json['value']['totalHits'])

            for m_row, r_row in zip(metadata, refs):
                results_map = dict()
                results_map['xip.reference'] = r_row[1]
                for li in m_row:
                    results_map[li['name']] = li['value']
                results_list.append(results_map)
            next_start = start_index + page_size

            if self.callback is not None:
                value = str(f'{len(results_list) + start_index}:{hits}')
                self.callback(value)

            search_results = self.SearchResult(metadata, refs, hits, results_list, next_start)
            return search_results
        elif results.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.search_index_filter(query, start_index, page_size, map_fields)
        else:
            print(f"search failed with error code: {results.status_code}")
            print(results.request.url)
            raise RuntimeError(results.status_code, f"search_index_filter failed")
