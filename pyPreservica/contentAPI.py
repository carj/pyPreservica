"""
pyPreservica ContentAPI module definition

A client library for the Preservica Repository web services Content API
https://us.preservica.com/api/content/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""

import csv
from io import BytesIO
from typing import Generator, Callable, Optional, Union
from pyPreservica.common import *

logger = logging.getLogger(__name__)

class SortOrder(Enum):
    asc = 1
    desc = 2

class Operator(Enum):
    IS = "IS"
    NOT = "NOT"

class Field:
    name: str
    value: Optional[Union[str, list[str]]] = None
    operator: Optional[Operator]
    sort_order: Optional[SortOrder]

    def __init__(self, name: str, value: Union[str, list[str]], operator: Optional[Operator]=Operator.IS, sort_order: Optional[SortOrder]=None):
        self.name = name
        self.value = value
        self.operator = operator
        self.sort_order = sort_order


class ContentAPI(AuthenticatedAPI):
    """
        The ContentAPI class provides the search interface to the Preservica repository.

    """


    def __init__(self, username: str|None = None, password: str|None = None, tenant: str|None = None, server: str|None = None,
                 use_shared_secret: bool = False, two_fa_secret_key: str|None = None,
                 protocol: str = "https", request_hook: Callable|None = None, credentials_path: str = 'credentials.properties'):
        """
        Initialise the ContentAPI client and authenticate against the Preservica server.

        Credentials are resolved in the following priority order: explicit keyword arguments,
        environment variables (``PRESERVICA_USERNAME``, ``PRESERVICA_PASSWORD``,
        ``PRESERVICA_TENANT``, ``PRESERVICA_SERVER``), and finally the ``credentials.properties``
        file at ``credentials_path``.

        :param username: Preservica account username (e-mail address).
        :type username: str or None
        :param password: Preservica account password.
        :type password: str or None
        :param tenant: Preservica tenant identifier.
        :type tenant: str or None
        :param server: Preservica server hostname (e.g. ``us.preservica.com``).
        :type server: str or None
        :param use_shared_secret: When ``True``, authenticate using a shared-secret token
            rather than username/password credentials.
        :type use_shared_secret: bool
        :param two_fa_secret_key: Base-32 TOTP secret key for two-factor authentication.
        :type two_fa_secret_key: str or None
        :param protocol: Transport protocol, either ``"https"`` (default) or ``"http"``.
        :type protocol: str
        :param request_hook: Optional callable that will be registered as a ``requests``
            session event hook, invoked before every HTTP request.
        :type request_hook: callable or None
        :param credentials_path: Path to a ``credentials.properties`` file used as a
            fallback credential source.
        :type credentials_path: str
        """

        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook, credentials_path)

        self.callback: Callable|None = None

    class SearchResult:
        def __init__(self, metadata, refs, hits, results_list, next_start):
            self.metadata = metadata
            self.refs = refs
            self.hits = int(hits)
            self.results_list = results_list
            self.next_start = next_start

    def search_callback(self, fn: Callable):
        """
        Register a progress callback that is invoked after each search page is fetched.

        The callback receives a single string argument formatted as
        ``"<fetched>:<total>"`` (e.g. ``"50:320"``), allowing callers to report
        or act on incremental search progress.

        :param fn: Callable that accepts one positional ``str`` argument.
        :type fn: callable
        """
        self.callback = fn

    def user_security_tags(self, with_permissions: bool = False):
        """
        Return the security tags available to the currently authenticated user.

        When ``with_permissions`` is ``False`` (the default) the returned dict maps
        each tag name to itself.  When ``True``, each tag name maps to the list of
        permission strings associated with that tag.

        Requires Preservica v6.3.2 or higher; raises ``RuntimeError`` on older
        servers.

        :param with_permissions: When ``True``, include the permissions list for
            each tag instead of just the tag name.
        :type with_permissions: bool
        :returns: Dictionary mapping security-tag names to their display name (or
            to a list of permission strings when ``with_permissions=True``).
        :rtype: dict
        :raises RuntimeError: If the server version is below v6.3.2 or the API
            call fails.
        """

        return self.security_tags_base(with_permissions=with_permissions)


    def full_text(self, reference: str) -> str|None:
        """
        Return the full-text index value for an Asset.

        If the Asset has been OCR'd or otherwise indexed for full-text search,
        this method returns the indexed text content.  The ``reference`` must
        identify an Asset (document type ``IO``); content objects and folders
        are not supported.

        :param reference: The UUID reference of the Asset whose full-text index
            value should be retrieved.
        :type reference: str
        :returns: The full-text index string for the Asset, or ``None`` if the
            reference is not found or does not correspond to an Asset.
        :rtype: str or None
        """

        hits = list(self.simple_search_list(query=f"id:{reference}",
                                  list_indexes=['xip.reference', 'xip.full_text', 'xip.document_type']))
        if len(hits) == 1:
            hit = hits[0]
            if (hit['xip.reference'] == reference) and (hit['xip.document_type'] == 'IO'):
                return str(hit['xip.full_text'])

        return None


    def object_details(self, entity_type, reference: str, exclude_dates: bool = False) -> dict:
        """
        Return the CMIS property bag for a single repository object.

        Retrieves all indexed metadata attributes stored against the object,
        such as ``cmis:name``, ``cmis:objectId``, and custom schema fields.
        Date-related properties (``cmis:createdBy``, ``cmis:creationDate``,
        ``cmis:lastModifiedBy``, ``cmis:lastModificationDate``) can be omitted
        by setting ``exclude_dates=True``.

        :param entity_type: The type of entity to look up.  Either an
            :class:`~pyPreservica.common.EntityType` enum value (e.g.
            ``EntityType.ASSET``) or the raw string representation used by the
            API (e.g. ``"IO"``).
        :type entity_type: EntityType or str
        :param reference: The UUID reference of the entity.
        :type reference: str
        :param exclude_dates: When ``True``, omits the four CMIS date/history
            properties from the returned dictionary.
        :type exclude_dates: bool
        :returns: Dictionary of CMIS property names to their values for the
            requested object.
        :rtype: dict
        :raises RuntimeError: If the reference is not found in the repository
            (HTTP 404), or if the API call fails for any other reason.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json'}
        if type(entity_type) == EntityType:
            params = {'id': f'sdb:{entity_type.value}|{reference}'}
        else:
            params = {'id': f'sdb:{entity_type}|{reference}'}

        if exclude_dates:
            params['excludeproperties'] = 'history'
        else:
            params['excludeproperties'] = ''

        request = self.session.get(f'{self.protocol}://{self.server}/api/content/object-details', params=params,
                                   headers=headers)
        if request.status_code == requests.codes.ok:
            return request.json()["value"]
        elif request.status_code == requests.codes.not_found:
            logger.error(f"The requested reference is not found in the repository: {reference}")
            raise RuntimeError(reference, "The requested reference is not found in the repository")
        else:
            logger.error(f"object_details failed with error code: {request.status_code}")
            raise RuntimeError(request.status_code, f"object_details failed with error code: {request.status_code}")


    def download_bytes(self, reference) -> BytesIO:
        """
        Download the access copy of an Asset and return it as an in-memory byte buffer.

        Streams the binary content from the Preservica content-download endpoint
        directly into a :class:`~io.BytesIO` object.  The buffer's position is
        reset to zero before it is returned so callers can read from it
        immediately.

        :param reference: The UUID reference of the Asset (Information Object) to
            download.
        :type reference: str
        :returns: An in-memory byte buffer containing the downloaded file content,
            seeked to position 0.
        :rtype: io.BytesIO
        :raises RuntimeError: If the reference is not found in the repository
            (HTTP 404), or if the download fails for any other reason.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream', 'X-STREAM-No-Retry': 'true'}
        params = {'id': f'sdb:IO|{reference}'}
        with self.session.get(f'{self.protocol}://{self.server}/api/content/download', params=params, headers=headers, stream=True) as req:
            if req.status_code == requests.codes.ok:
                file_bytes = BytesIO()
                for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                    file_bytes.write(chunk)
                file_bytes.seek(0)
                return file_bytes
            elif req.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.download_bytes(reference)
            elif req.status_code == requests.codes.not_found:
                logger.error(f"The requested asset reference is not found in the repository: {reference}")
                raise RuntimeError(reference, "The requested reference is not found in the repository")
            else:
                logger.error(f"download failed with error code: {req.status_code}")
                raise RuntimeError(req.status_code, f"download failed with error code: {req.status_code}")


    def download(self, reference, filename) -> str:
        """
        Download the access copy of an Asset and save it to a local file.

        Streams the binary content from the Preservica content-download endpoint
        directly to disk, flushing each chunk as it is written.

        :param reference: The UUID reference of the Asset (Information Object) to
            download.
        :type reference: str
        :param filename: Local filesystem path where the downloaded content will
            be written.
        :type filename: str
        :returns: The ``filename`` path that was written to.
        :rtype: str
        :raises RuntimeError: If the reference is not found in the repository
            (HTTP 404), or if the download fails for any other reason.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream', 'X-STREAM-No-Retry': 'true'}
        params = {'id': f'sdb:IO|{reference}'}
        with self.session.get(f'{self.protocol}://{self.server}/api/content/download', params=params, headers=headers,
                              stream=True) as req:
            if req.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                        file.flush()
                return filename
            elif req.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.download(reference, filename)
            elif req.status_code == requests.codes.not_found:
                logger.error(f"The requested asset reference is not found in the repository: {reference}")
                raise RuntimeError(reference, "The requested reference is not found in the repository")
            else:
                logger.error(f"download failed with error code: {req.status_code}")
                raise RuntimeError(req.status_code, f"download failed with error code: {req.status_code}")

    def thumbnail_bytes(self, entity_type, reference: str, size: Thumbnail = Thumbnail.LARGE) -> BytesIO:
        """
        Retrieve the thumbnail image for a repository entity and return it as an in-memory byte buffer.

        Downloads the PNG thumbnail generated by Preservica for the given entity.
        The buffer's position is reset to zero before it is returned so callers
        can read or pass it directly to image-processing libraries.

        :param entity_type: The type of entity whose thumbnail is requested.
            Either an :class:`~pyPreservica.common.EntityType` enum value or the
            corresponding raw string used by the API (e.g. ``"IO"``, ``"SO"``).
        :type entity_type: EntityType or str
        :param reference: The UUID reference of the entity.
        :type reference: str
        :param size: The desired thumbnail size.  One of
            :attr:`~pyPreservica.common.Thumbnail.SMALL`,
            :attr:`~pyPreservica.common.Thumbnail.MEDIUM`, or
            :attr:`~pyPreservica.common.Thumbnail.LARGE` (default).
        :type size: Thumbnail
        :returns: An in-memory byte buffer containing the PNG thumbnail image,
            seeked to position 0.
        :rtype: io.BytesIO
        :raises RuntimeError: If the reference is not found in the repository
            (HTTP 404), or if the thumbnail retrieval fails for any other reason.
        """
        headers = {HEADER_TOKEN: self.token, 'accept': 'image/png', 'X-STREAM-No-Retry': 'true'}
        params = {'id': f'sdb:{entity_type}|{reference}', 'size': f'{size.value}'}
        with self.session.get(f'{self.protocol}://{self.server}/api/content/thumbnail', params=params, headers=headers, stream=True) as req:
            if req.status_code == requests.codes.ok:
                file_bytes = BytesIO()
                for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                    file_bytes.write(chunk)
                file_bytes.seek(0)
                return file_bytes
            elif req.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.thumbnail_bytes(entity_type, reference, size)
            elif req.status_code == requests.codes.not_found:
                logger.error(req.content.decode("utf-8"))
                logger.error(f"The requested reference is not found in the repository: {reference}")
                raise RuntimeError(reference, "The requested reference is not found in the repository")
            else:
                logger.error(f"thumbnail failed with error code: {req.status_code}")
                raise RuntimeError(req.status_code, f"thumbnail failed with error code: {req.status_code}")

    def thumbnail(self, entity_type, reference, filename, size=Thumbnail.LARGE) -> str:
        """
        Retrieve the thumbnail image for a repository entity and save it to a local file.

        Downloads the PNG thumbnail generated by Preservica for the given entity
        and writes it to ``filename`` on the local filesystem.

        :param entity_type: The type of entity whose thumbnail is requested.
            Either an :class:`~pyPreservica.common.EntityType` enum value or the
            corresponding raw string used by the API (e.g. ``"IO"``, ``"SO"``).
        :type entity_type: EntityType or str
        :param reference: The UUID reference of the entity.
        :type reference: str
        :param filename: Local filesystem path where the PNG thumbnail will be
            written.
        :type filename: str
        :param size: The desired thumbnail size.  One of
            :attr:`~pyPreservica.common.Thumbnail.SMALL`,
            :attr:`~pyPreservica.common.Thumbnail.MEDIUM`, or
            :attr:`~pyPreservica.common.Thumbnail.LARGE` (default).
        :type size: Thumbnail
        :returns: The ``filename`` path that was written to.
        :rtype: str
        :raises RuntimeError: If the reference is not found in the repository
            (HTTP 404), or if the thumbnail retrieval fails for any other reason.
        """
        headers = {HEADER_TOKEN: self.token, 'accept': 'image/png', 'X-STREAM-No-Retry': 'true'}
        params = {'id': f'sdb:{entity_type}|{reference}', 'size': f'{size.value}'}
        with self.session.get(f'{self.protocol}://{self.server}/api/content/thumbnail', params=params, headers=headers,  stream=True) as req:
            if req.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                        file.flush()
                return filename
            elif req.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.thumbnail(entity_type, reference, filename, size)
            elif req.status_code == requests.codes.not_found:
                logger.error(req.content.decode("utf-8"))
                logger.error(f"The requested reference is not found in the repository: {reference}")
                raise RuntimeError(reference, "The requested reference is not found in the repository")
            else:
                logger.error(f"thumbnail failed with error code: {req.status_code}")
                raise RuntimeError(req.status_code, f"thumbnail failed with error code: {req.status_code}")

    def indexed_fields(self) -> dict:
        """
        Return all search-index field names and their associated URIs.

        Queries the Preservica ``/api/content/indexed-fields`` endpoint and
        returns a dictionary mapping each field's short dotted name (e.g.
        ``"xip.title"``, ``"cmis:name"``) to its full schema URI.  This is
        useful for discovering which fields are available when building search
        queries or filter dictionaries for the various search methods.

        :returns: Dictionary mapping indexed field names (``"<schema>.<index>"``
            format) to their full schema URI strings.
        :rtype: dict
        :raises RuntimeError: If the API call fails.
        """
        headers = {HEADER_TOKEN: self.token}
        results = self.session.get(f'{self.protocol}://{self.server}/api/content/indexed-fields', headers=headers)
        if results.status_code == requests.codes.ok:
            fields = {}
            for ob in results.json()["value"]:
                field = f'{ob["shortName"]}.{ob["index"]}'
                fields[field] = ob["uri"]
            return fields
        else:
            logger.error(f"indexed_fields failed with error code: {results.status_code}")
            raise RuntimeError(results.status_code, f"indexed_fields failed with error code: {results.status_code}")

    def simple_search_csv(self, query: str = "%", page_size: int = 50, csv_file="search.csv",
                          list_indexes: list|None = None):
        """
        Run a simple keyword search and write all results to a CSV file.

        Executes the same query as :meth:`simple_search_list` but instead of
        returning a generator it writes every result row to a UTF-8 encoded CSV
        file.  The first column is always ``xip.reference``.  If ``list_indexes``
        is omitted, the default set of fields
        (``xip.reference``, ``xip.title``, ``xip.description``,
        ``xip.document_type``, ``xip.parent_ref``, ``xip.security_descriptor``)
        is used as both the column headers and the requested metadata fields.

        :param query: Lucene-style search expression.  Use ``"%"`` (default) to
            match all objects.
        :type query: str
        :param page_size: Number of results to fetch per API request (default 50).
        :type page_size: int
        :param csv_file: Path to the output CSV file (default ``"search.csv"``).
        :type csv_file: str
        :param list_indexes: Optional list of index field names to include as
            columns.  ``xip.reference`` is always prepended if not present.
        :type list_indexes: list or None
        """
        if list_indexes is None or len(list_indexes) == 0:
            metadata_fields = ["xip.reference", "xip.title", "xip.description", "xip.document_type",
                               "xip.parent_ref", "xip.security_descriptor"]
        else:
            metadata_fields = list(list_indexes)
        if "xip.reference" not in metadata_fields:
            metadata_fields.insert(0, "xip.reference")
        with open(csv_file, newline='', mode="wt", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=metadata_fields)
            writer.writeheader()
            writer.writerows(self.simple_search_list(query, page_size, metadata_fields))

    def simple_search_list(self, query: str = "%", page_size: int = 50, list_indexes: list|None = None) -> Generator:
        """
        Run a simple keyword search and yield all matching result rows as dictionaries.

        Issues paginated requests to the Preservica search endpoint and lazily
        yields each result row as a ``dict`` whose keys are the requested index
        field names.  ``xip.reference`` is always present as the first key.
        Pagination continues automatically until all matching objects have been
        yielded.

        If a progress callback has been registered via :meth:`search_callback`,
        it is called after each page with the current progress string.

        :param query: Lucene-style search expression.  Use ``"%"`` (default) to
            match all objects.
        :type query: str
        :param page_size: Number of results to fetch per API request (default 50).
        :type page_size: int
        :param list_indexes: List of index field names to retrieve for each
            result.  When omitted, the default set
            (``xip.title``, ``xip.description``, ``xip.document_type``,
            ``xip.parent_ref``, ``xip.security_descriptor``) is used.
            ``xip.reference`` is always included.
        :type list_indexes: list or None
        :returns: Generator that yields one ``dict`` per matching object.
        :rtype: Generator[dict, None, None]
        :raises RuntimeError: If the API call fails.
        """

        search_result = self._simple_search(query, 0, page_size, list_indexes)
        for e in search_result.results_list:
            yield e
        found = len(search_result.results_list)
        while search_result.hits > found:
            search_result = self._simple_search(query, found, page_size, list_indexes)
            for e in search_result.results_list:
                yield e
            found = found + len(search_result.results_list)

    def _simple_search(self, query: str = "%", start_index: int = 0, page_size: int = 10, list_indexes: list|None = None) -> SearchResult:
        start_from = str(start_index)
        headers = {'Content-Type': 'application/x-www-form-urlencoded', HEADER_TOKEN: self.token}
        query_term = ('{ "q":  "%s" }' % query)
        if list_indexes is None or len(list_indexes) == 0:
            metadata_fields = "xip.title,xip.description,xip.document_type,xip.parent_ref,xip.security_descriptor"
        else:
            metadata_fields = ','.join(list_indexes)
        payload = {'start': start_from, 'max': str(page_size), 'metadata': metadata_fields, 'q': query_term}
        results = self.session.post(f'{self.protocol}://{self.server}/api/content/search', data=payload,
                                    headers=headers)
        results_list = []
        if results.status_code == requests.codes.ok:
            json_doc = results.json()
            metadata = json_doc['value']['metadata']
            refs = list(json_doc['value']['objectIds'])
            refs = list(map(lambda x: content_api_identifier_to_type(x), refs))
            hits = int(json_doc['value']['totalHits'])

            for m_row, r_row in zip(metadata, refs):
                results_map = {'xip.reference': r_row[1]}
                for li in m_row:
                    results_map[li['name']] = li['value']
                results_list.append(results_map)
            next_start = start_index + page_size

            if self.callback is not None:
                value = str(f'{len(results_list) + start_index}:{hits}')
                self.callback(value)

            search_results = self.SearchResult(metadata, refs, hits, results_list, next_start)
            return search_results
        else:
            logger.error(f"search failed with error code: {results.status_code}")
            raise RuntimeError(results.status_code, f"simple_search failed with error code: {results.status_code}")

    def search_index_filter_csv(self, query: str = "%", csv_file="search.csv", page_size: int = 50,
                                filter_values: dict|None = None,
                                sort_values: dict|None = None):
        """
        Run a filtered search and write all results to a CSV file.

        Executes the same query as :meth:`search_index_filter_list` but writes
        every result row to a UTF-8 encoded CSV file instead of returning a
        generator.  Column headers are derived from the keys of
        ``filter_values``; ``xip.reference`` is always the first column.

        :param query: Lucene-style search expression.  Use ``"%"`` (default) to
            match all objects.
        :type query: str
        :param csv_file: Path to the output CSV file (default ``"search.csv"``).
        :type csv_file: str
        :param page_size: Number of results to fetch per API request (default 50).
        :type page_size: int
        :param filter_values: Dictionary mapping index field names to filter
            values.  An empty string value (``""``) means "return this field but
            do not restrict by value".  A non-empty string or list of strings
            restricts results to objects whose field matches one of the supplied
            values.  ``xip.reference`` is added automatically if absent.
        :type filter_values: dict or None
        :param sort_values: Optional dictionary mapping index field names to sort
            directions.  Values starting with ``"d"`` (case-insensitive) sort
            descending; all other values sort ascending.
        :type sort_values: dict or None
        """
        if filter_values is None:
            filter_values = {}
        if "xip.reference" not in filter_values:
            filter_values["xip.reference"] = ""

        header_fields = list(filter_values.keys())
        index = header_fields.index("xip.reference")
        header_fields.insert(0, header_fields.pop(index))
        with open(csv_file, newline='', mode="wt", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=header_fields)
            writer.writeheader()
            writer.writerows(self.search_index_filter_list(query, page_size, filter_values, sort_values))

    def search_fields(self, query: str = "%",  fields: list[Field]|None=None,  page_size: int = 25) -> Generator:
        """
        Run a structured search using :class:`Field` objects and yield all matching result rows.

        Provides a richer search interface than :meth:`simple_search_list` or
        :meth:`search_index_filter_list` by accepting a list of :class:`Field`
        instances that can carry value filters, ``IS``/``NOT`` operators, and
        sort orders.  Results are paginated automatically and yielded lazily.

        Requires Preservica v7.5 or higher; raises ``RuntimeError`` on older
        servers.

        :param query: Lucene-style search expression.  Use ``"%"`` (default) to
            match all objects.
        :type query: str
        :param fields: List of :class:`Field` instances specifying which index
            fields to retrieve and optionally filter or sort by.  When
            ``None`` or empty, only ``xip.title`` is requested with no filters.
        :type fields: list[Field] or None
        :param page_size: Number of results to fetch per API request (default 25).
        :type page_size: int
        :returns: Generator that yields one ``dict`` per matching object, with
            ``xip.reference`` always present as a key.
        :rtype: Generator[dict, None, None]
        :raises RuntimeError: If the server version is below v7.5 or the API
            call fails.
        """

        if self.major_version < 7 or (self.major_version == 7 and self.minor_version < 5):
            raise RuntimeError("search_fields API call is not available when connected to a v7.5 System")

        search_result = self._search_fields(query=query, fields=fields, start_index=0, page_size=page_size)
        for e in search_result.results_list:
            yield e
        found = len(search_result.results_list)
        while search_result.hits > found:
            search_result = self._search_fields(query=query, fields=fields, start_index=found, page_size=page_size)
            for e in search_result.results_list:
                yield e
            found = found + len(search_result.results_list)

    def _search_fields(self, query: str = "%", fields: list[Field]|None=None, start_index: int = 0, page_size: int = 25) -> SearchResult:

        start_from = str(start_index)
        headers = {'Content-Type': 'application/x-www-form-urlencoded', HEADER_TOKEN: self.token}

        if fields is None:
            fields = []

        field_list = []
        sort_list = []
        metadata_elements = []
        for field in fields:
            metadata_elements.append(field.name)
            if field.value is None or field.value == "":
                field_list.append('{' f' "name": "{field.name}", "values": [] ' + '}')
            else:

                if isinstance(field.value, str):
                    if field.operator == Operator.NOT:
                        field_list.append(
                            '{' f' "name": "{field.name}", "values": ["{field.value}"], "operator": "NOT" ' + '}')
                    else:
                        field_list.append('{' f' "name": "{field.name}", "values":[ "{field.value}" ]' '}')
                if isinstance(field.value, list):
                    values = [f'"{w}"' for w in field.value]
                    v:str = f' {",".join(values)} '
                    if field.operator == Operator.NOT:
                        field_list.append(
                            '{' f' "name": "{field.name}", "values": [ {v} ], "operator": "NOT" ' + '}')
                    else:
                        field_list.append('{' f' "name": "{field.name}", "values":[ {v} ]' '}')


            if field.sort_order is not None:
                sort_list.append(f'{{"sortFields": ["{field.name}"], "sortOrder": "{field.sort_order.name}"}}')


        filter_terms = ','.join(field_list)

        if len(sort_list) == 0:
            query_term = ('{ "q":  "%s",  "fields":  [ %s ] }' % (query, filter_terms))
        else:
            sort_terms = ','.join(sort_list)
            query_term = ('{ "q":  "%s",  "fields":  [ %s ],  "sort": [ %s ]}' % (query, filter_terms, sort_terms))

        if len(metadata_elements) == 0:
            metadata_elements.append("xip.title")


        payload = {'start': start_from, 'max': str(page_size), 'metadata': list(metadata_elements), 'q': query_term}
        logger.debug(payload)
        results = self.session.post(f'{self.protocol}://{self.server}/api/content/search', data=payload,
                                    headers=headers)
        results_list = []
        if results.status_code == requests.codes.ok:
            json_doc = results.json()
            metadata = json_doc['value']['metadata']
            refs = list(json_doc['value']['objectIds'])
            refs = list(map(lambda x: content_api_identifier_to_type(x), refs))
            hits = int(json_doc['value']['totalHits'])

            for m_row, r_row in zip(metadata, refs):
                results_map = {'xip.reference': r_row[1]}
                for li in m_row:
                    results_map[li['name']] = li['value']
                results_list.append(results_map)
            next_start = start_index + page_size

            if self.callback is not None:
                value = str(f'{len(results_list) + start_index}:{hits}')
                self.callback(value)

            search_results = self.SearchResult(metadata, refs, hits, results_list, next_start)
            return search_results
        else:
            logger.error(f"search failed with error code: {results.status_code}")
            raise RuntimeError(results.status_code, f"search_index_filter failed")

    def search_index_filter_list(self, query: str = "%", page_size: int = 25, filter_values: dict|None = None,
                                 sort_values: dict|None = None) -> Generator:
        """
        Run a filtered search and yield all matching result rows as dictionaries.

        Issues paginated requests to the Preservica search endpoint, applying
        per-field value filters and optional sort criteria.  Pagination
        continues automatically until all matching objects have been yielded.
        Each result row is a ``dict`` whose keys come from ``filter_values``,
        with ``xip.reference`` always present.

        If a progress callback has been registered via :meth:`search_callback`,
        it is called after each page with the current progress string.

        :param query: Lucene-style search expression.  Use ``"%"`` (default) to
            match all objects.
        :type query: str
        :param page_size: Number of results to fetch per API request (default 25).
        :type page_size: int
        :param filter_values: Dictionary mapping index field names to filter
            values.  An empty string value (``""``) means "return this field but
            do not restrict by value".  A non-empty string or list of strings
            restricts results to objects whose field matches one of the supplied
            values.
        :type filter_values: dict or None
        :param sort_values: Optional dictionary mapping index field names to sort
            directions.  Values starting with ``"d"`` (case-insensitive) sort
            descending; all other values sort ascending.
        :type sort_values: dict or None
        :returns: Generator that yields one ``dict`` per matching object.
        :rtype: Generator[dict, None, None]
        :raises RuntimeError: If the API call fails.
        """
        search_result = self._search_index_filter(query, 0, page_size, filter_values, sort_values)
        for e in search_result.results_list:
            yield e
        found = len(search_result.results_list)
        while search_result.hits > found:
            search_result = self._search_index_filter(query, found, page_size, filter_values, sort_values)
            for e in search_result.results_list:
                yield e
            found = found + len(search_result.results_list)

    def search_index_filter_hits(self, query: str = "%", filter_values: dict|None = None) -> int:
        """
        Run a filtered search and return only the total number of matching objects.

        Performs the same field-filtered query as :meth:`search_index_filter_list`
        but fetches only a minimal page (10 results) and returns the
        ``totalHits`` count reported by the API, without yielding the actual
        result rows.  This is useful for counting matches cheaply before
        deciding whether to retrieve the full result set.

        :param query: Lucene-style search expression.  Use ``"%"`` (default) to
            match all objects.
        :type query: str
        :param filter_values: Dictionary mapping index field names to filter
            values.  An empty string value (``""``) means "do not restrict by
            value".  A non-empty string or list of strings restricts the count
            to objects whose field matches one of the supplied values.  When
            ``None``, defaults to ``{"xip.reference": "", "xip.title": ""}``.
        :type filter_values: dict or None
        :returns: Total number of repository objects that match the query and
            filters.
        :rtype: int
        :raises RuntimeError: If the API call fails.
        """
        start_from = str(0)
        headers = {'Content-Type': 'application/x-www-form-urlencoded', HEADER_TOKEN: self.token}

        if filter_values is None:
            filter_values = {'xip.reference': '', 'xip.title': ''}

        field_list = []
        for key, value in filter_values.items():
            if value == "":
                field_list.append('{' f' "name": "{key}", "values": [] ' + '}')
            else:
                if isinstance(value, str):
                    field_list.append('{' f' "name": "{key}", "values": ["{value}"] ' + '}')
                if isinstance(value, list):
                    values = [f'"{w}"' for w in value]
                    v: str = f' {",".join(values)} '
                    field_list.append('{' f' "name": "{key}", "values":[ {v} ]' '}')

        filter_terms = ','.join(field_list)

        query_term = ('{ "q":  "%s",  "fields":  [ %s ] }' % (query, filter_terms))

        payload = {'start': start_from, 'max': str(10), 'metadata': list(filter_values.keys()), 'q': query_term}
        results = self.session.post(f'{self.protocol}://{self.server}/api/content/search', data=payload,
                                    headers=headers)
        if results.status_code == requests.codes.ok:
            json_doc = results.json()
            return int(json_doc['value']['totalHits'])
        else:
            logger.error(f"search failed with error code: {results.status_code}")
            raise RuntimeError(results.status_code, f"_search_index_filter_hits failed")

    def _search_index_filter(self, query: str = "%", start_index: int = 0, page_size: int = 25,
                             filter_values: dict|None = None, sort_values: dict|None = None) -> SearchResult:
        start_from = str(start_index)
        headers = {'Content-Type': 'application/x-www-form-urlencoded', HEADER_TOKEN: self.token}

        if filter_values is None:
            filter_values = {}

        field_list = []
        for key, value in filter_values.items():
            if value == "":
                field_list.append('{' f' "name": "{key}", "values": [] ' + '}')
            else:
                if isinstance(value, str):
                    field_list.append('{' f' "name": "{key}", "values": ["{value}"] ' + '}')
                if isinstance(value, list):
                    values = [f'"{w}"' for w in value]
                    v: str = f' {",".join(values)} '
                    field_list.append('{' f' "name": "{key}", "values":[ {v} ]' '}')

        filter_terms = ','.join(field_list)

        if sort_values is None:
            query_term = ('{ "q":  "%s",  "fields":  [ %s ] }' % (query, filter_terms))
        else:
            sort_list = []
            for key, value in sort_values.items():
                direction = "asc"
                if str(value).lower().startswith("d"):
                    direction = "desc"
                sort_list.append(f'{{"sortFields": ["{key}"], "sortOrder": "{direction}"}}')
            sort_terms = ','.join(sort_list)
            query_term = ('{ "q":  "%s",  "fields":  [ %s ],  "sort": [ %s ]}' % (query, filter_terms, sort_terms))

        payload = {'start': start_from, 'max': str(page_size), 'metadata': list(filter_values.keys()), 'q': query_term}
        logger.debug(payload)
        results = self.session.post(f'{self.protocol}://{self.server}/api/content/search', data=payload,
                                    headers=headers)
        results_list = []
        if results.status_code == requests.codes.ok:
            json_doc = results.json()
            metadata = json_doc['value']['metadata']
            refs = list(json_doc['value']['objectIds'])
            refs = list(map(lambda x: content_api_identifier_to_type(x), refs))
            hits = int(json_doc['value']['totalHits'])

            for m_row, r_row in zip(metadata, refs):
                results_map = {'xip.reference': r_row[1]}
                for li in m_row:
                    results_map[li['name']] = li['value']
                results_list.append(results_map)
            next_start = start_index + page_size

            if self.callback is not None:
                value = str(f'{len(results_list) + start_index}:{hits}')
                self.callback(value)

            search_results = self.SearchResult(metadata, refs, hits, results_list, next_start)
            return search_results
        else:
            logger.error(f"search failed with error code: {results.status_code}")
            raise RuntimeError(results.status_code, f"search_index_filter failed")

    class ReportProgressCallBack:
        def __init__(self):
            self.current = 0
            self.total = 0
            self._lock = threading.Lock()

        def __call__(self, value):
            with self._lock:
                values = value.split(":")
                self.total = int(values[1])
                self.current = int(values[0])
                if self.total == 0:
                    percentage = 100.0
                else:
                    percentage = (self.current / self.total) * 100
                sys.stdout.write("\rProcessing Hits %s from %s  (%.2f%%)" % (self.current, self.total, percentage))
                sys.stdout.flush()
