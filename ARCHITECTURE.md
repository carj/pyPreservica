# pyPreservica Architectural Design

**Repository:** [carj/pyPreservica](https://github.com/carj/pyPreservica)  
**Package:** `pyPreservica`  
**Status:** Architecture of the current `master` implementation  
**Latest reviewed commit:** `a31e59487dd524528acbc0869670dc1504286af1`

## 1. Purpose

pyPreservica is an Apache-2.0 licensed Python SDK for the Preservica REST APIs. It gives applications Python classes and helpers for repository entity operations, search, uploads and ingest packages, metadata and schema administration, workflows, retention, webhooks, reporting, and authority management.

It is a third-party client library rather than a Preservica server application. Public API classes are exposed from `pyPreservica/__init__.py`, while HTTP communication and domain models are implemented in this repository.

## 2. Architectural Goals

- **Usability:** allow scripts to import API clients and domain objects directly without managing tokens or XML endpoint details.
- **Coverage:** map Preservica API areas into focused client classes.
- **Preservica compatibility:** support changing server versions and version-specific XML namespaces.
- **Resilience:** recover expired access tokens and retry selected HTTP failures.
- **Streaming:** support large downloads and cloud uploads without requiring complete byte arrays.
- **Portability:** run on supported Python versions and AWS or Azure Preservica deployments.
- **Observability:** provide logging and optional progress callbacks.

## 3. System Context

```text
Python application / script
           |
           v
     pyPreservica SDK
           |
  +--------+-----------------------------+
  |                                     |
  v                                     v
Preservica HTTP REST APIs          AWS S3 / Azure Blob
(Entity, Content, Upload, Admin,     (ingest packages and
 Security, Workflow, etc.)          upload-source storage)
```

The library also uses the local filesystem for credentials, package generation, downloads, CSV/XML/XSD artifacts, fixity computation, and report output.

## 4. Public Package Structure

`pyPreservica/__init__.py` is the package facade. It re-exports the common authentication and model types plus the principal API clients and package/report helper types:

- `common.py` — shared authentication, HTTP infrastructure, entity models, pagination, fixity, progress callbacks, and exceptions.
- `entityAPI.py` — folders, assets, content objects, representations, generations, bitstreams, metadata, identifiers, relationships, events, and deletion.
- `contentAPI.py` — content search, indexed fields, downloads, thumbnails, and object details.
- `uploadAPI.py` — XIP ingest package generation and AWS/Azure upload orchestration.
- `adminAPI.py` — users, roles, security tags, schemas, XML documents, and transforms.
- `authorityAPI.py` — authority records and authority-table operations.
- `mdformsAPI.py` — metadata groups and metadata form fields.
- `settingsAPI.py` — Preservica settings operations.
- `workflowAPI.py` — workflows and workflow processes.
- `retentionAPI.py` — retention policies, assignments, and legal holds.
- `parAPI.py` — Preservation Action Registry operations.
- `reportingAPI.py` — storage usage and duplicate-content reports.
- `monitorAPI.py` — system monitoring and status.
- `webHooksAPI.py` — webhook handlers, including Flask and Lambda adapters.
- `opex.py` — OPEX package helpers.

## 5. Core Architecture

### 5.1 Facade and API clients

The package uses a thin-facade approach. Callers normally import from `pyPreservica`, then construct one of the domain API clients:

```python
EntityAPI()
ContentAPI()
UploadAPI()
AdminAPI()
ReportingAPI()
```

Each client is intentionally service-oriented rather than exposing one universal low-level HTTP interface. Public methods represent Preservica operations, while private methods implement endpoint, XML, and pagination details.

### 5.2 Shared authentication base

`AuthenticatedAPI` in `common.py` is the base for API clients. It owns:

- credentials resolved from constructor arguments, environment variables, or `credentials.properties`;
- password, 2FA, and shared-secret authentication;
- a primary `requests.Session` and a separate token acquisition session;
- a Preservica access token in the `Preservica-Access-Token` header;
- server major/minor/patch version discovery;
- version-specific XIP, Entity, Security, Admin, and retention XML namespaces;
- user roles;
- automatic 401 token refresh;
- HTTP timeouts and retries for transient gateway responses;
- thread synchronization around token refresh.

The authentication flow is a side-effectful constructor operation: clients acquire a token and discover server version and roles before exposing normal operations.

### 5.3 Domain model

The common module defines lightweight domain objects for Preservica entities:

- `Entity` as the base;
- `Folder`, `Asset`, and `ContentObject`;
- `Representation`, `Generation`, and `Bitstream`;
- `ExternIdentifier`, `Relationship`, `PagedSet`, and `IntegrityCheck`;
- enums for entity, representation, relationship, thumbnail, and async-progress types.

Most entity objects retain references and metadata URLs rather than caching the complete repository graph. This lets API methods lazily traverse representations, content objects, generations, and bitstreams.

### 5.4 HTTP and data representation

The code uses `requests` sessions for JSON, form, XML, and binary communication. Responses are mostly parsed as XML or JSON, with some download operations streaming bytes.

The entity hierarchy is represented using Preservica XIP XML and Entity API XML namespaces. XML construction and parsing are centralized in API modules, especially `common.py`, `entityAPI.py`, and `uploadAPI.py`.

### 5.5 Pagination

Paginated operations use `PagedSet` or page URLs returned by Preservica. Public methods frequently expose lazy generators that continue fetching pages as callers iterate.

Examples include entity descendants/events and content search. This avoids eagerly loading large result sets and permits callback reporting during search or report scans.

## 6. Component Responsibilities

### Entity management

`EntityAPI` is the primary repository interaction client. It is responsible for:

- asset, folder, and content-object lookup;
- hierarchy traversal and recursive descendants;
- metadata add/update/delete;
- identifiers and relationships;
- representations and generations;
- streaming downloads and range resume;
- thumbnails and preview content;
- OPEX export and event workflows;
- entity moves and security-tag changes;
- manager-approved asset/folder deletion.

Long-running operations return process IDs or block through sync wrappers that poll Preservica progress endpoints.

### Content search and retrieval

`ContentAPI` wraps the Content API and supports:

- simple keyword search;
- indexed-field discovery;
- field filters and sorting;
- natural-language queries where supported;
- CSV export;
- full-text lookup;
- thumbnails and access downloads;
- object detail property bags.

Search methods use structured dictionaries or `Field` objects and serialize them into the Content API search payload.

### Upload and ingest

`UploadAPI` combines local package construction with remote transfer:

1. Package helpers build XIP `metadata.xml`, UUID references, representations, content objects, generations, metadata, identifiers, and fixities.
2. File content is copied into a package directory.
3. The package is optionally compressed to ZIP.
4. `upload_zip_package` uploads directly to the Preservica package upload bucket.
5. Upload to configured AWS S3 or Azure Blob upload sources is supported by separate methods.

AWS uploads use boto3/S3 transfer and refreshable credentials. Azure uploads use SAS credentials and `ContainerClient`. Package upload credentials are refreshed during long transfers, and multipart chunk sizes increase for larger files.

The package helper family supports:

- `simple_asset_package`;
- `complex_asset_package`;
- `generic_asset_package`;
- `multi_asset_package`.

It also provides CSV-to-XSD, CSV-to-XML, CMIS XSLT, and custom search-index generation helpers.

### Administrative services

`AdminAPI` contains role-gated operations for users, roles, security tags, schemas, XML documents, and XSLT transforms. Before privileged calls, it checks the authenticated user's roles and uses explicit Preservica role groups such as manager, user-manager, and config-manager roles.

### Reporting

`ReportingAPI` creates storage and duplicate-content reports. Repository reports share `RepositoryReport` behavior:

- Entity API traversal;
- thread-pool asset processing;
- optional console progress;
- JSON/CSV/HTML output;
- server/tenant/scanned-time metadata.

`StorageUsageReport` builds a folder/asset tree, totals active bitstream sizes, and renders a self-contained sunburst HTML report.

`DuplicateContentReport` compares normalized size/fixity values, identifies duplicate groups, and renders searchable HTML and CSV output.

## 7. Runtime Flows

### Authentication and request flow

```text
API client construction
  -> resolve credentials
  -> obtain access token
  -> discover server version
  -> derive XML namespaces
  -> retrieve current roles
  -> create API client

Operation
  -> construct endpoint and XML/JSON/form payload
  -> call requests.Session
  -> on 401: refresh token and retry
  -> on 502/503/504: retry via HTTPAdapter
  -> parse response or raise HTTPException
```

### Entity lookup

```text
EntityAPI.asset(reference)
  -> GET /api/entity/information-objects/{reference}
  -> parse XIP entity XML
  -> construct Asset with metadata URLs and parent reference
```

Subsequent representation traversal is separate and lazy. `representations()` fetches and parses the representation set, and content/generation/bitstream calls follow referenced URLs.

### Upload flow

```text
Package helper
  -> validate files and parent
  -> create XIP XML and UUIDs
  -> compute fixity
  -> copy content files
  -> create ZIP package

UploadAPI
  -> obtain/refresh token credentials
  -> select Preservica S3 or configured cloud source
  -> transfer package
  -> optionally delete local package
  -> return Preservica ingest progress token
```

## 8. Dependencies

The principal runtime dependencies declared in `setup.py` are:

- `requests` and `certifi` — HTTP and certificates;
- `boto3`, `botocore`, and `s3transfer` — AWS S3 uploads;
- `azure-storage-blob` — Azure Blob uploads;
- `pyrate-limiter` — upload rate limiting;
- `pyotp` — two-factor authentication;
- `python-dateutil` — date parsing;
- `tqdm` — progress display;
- `remotezip` — remote ZIP access in entity content helpers;
- `urllib3` — retry adapter support.

Documentation adds Sphinx themes and Google Analytics support.

## 9. Version and Compatibility Strategy

The SDK dynamically determines the connected Preservica server version and then selects namespace URIs and availability guards. Individual methods reject operations unsupported by older server versions.

This is a compatibility bridge rather than a separate adapter hierarchy. It keeps public clients relatively stable while embedding server-version checks at operation boundaries.

## 10. Error Handling

The library defines domain exceptions in `common.py`:

- `HTTPException` for non-success API responses;
- `ReferenceNotFoundException` for entity 404 lookups;
- `RuntimeError` for credential, role, server-version, upload, parsing, and package errors.

Most API modules include method names and response bodies in exceptions. Callers should treat HTTP status and method context as retryable or configuration diagnostics rather than relying only on exception text.

## 11. Concurrency and Scalability

- Token refresh is protected by a lock.
- Search and entity traversal are lazy and page-oriented.
- Reporting scans use a bounded `ThreadPoolExecutor` for asset processing.
- Upload progress callbacks may be invoked in transfer threads.
- Large downloads support chunking and range retries.
- Large uploads use multipart transfer and dynamic chunk-size selection.

The SDK is generally stateful per client instance, with a shared session and mutable token. Separate client instances are appropriate for independent threads or credentials.

## 12. Security Boundaries

- Credentials may be passed by code, environment variables, or local files; caller applications must protect them.
- Access tokens are held in memory and sent as Preservica-specific headers.
- Shared-secret authentication hashes a tenant/user/timestamp credential payload.
- 2FA secrets are held in memory and used to produce TOTP values.
- Manager credentials are read from `credentials.properties` only for operations requiring two-user approval.
- Cloud upload credentials are temporary and obtained through Preservica upload APIs.
- The XML and package helpers do not provide an external sandbox: package paths and metadata are local filesystem operations.

## 13. Testing and Delivery

The repository uses pytest-style tests in `tests/`, organized around API areas and package behavior. Many tests depend on a configured Preservica environment and credentials, as shown by `EntityAPI()` construction in tests.

The only load-bearing GitHub Actions workflow is CodeQL for Python, running on pushes and pull requests to `master` and weekly. Read the Docs builds Sphinx documentation using Python 3.12 and `docs/requirements.txt`.

The package is distributed through setup.py-based packaging and supports Python 3.10 through 3.15 classifiers in the manifest.

## 14. Known Architectural Constraints

1. **Monolithic API modules:** some modules, especially `entityAPI.py` and `uploadAPI.py`, are large and mix endpoint calls, XML transformation, local file operations, and workflows.
2. **Wildcard exports:** `__init__.py` relies on `common.py` wildcard imports, so the public namespace and dependency surface are broad.
3. **Implicit credential discovery:** constructor credentials and environment/config fallback increase convenience but make configuration precedence important.
4. **Mutable HTTP state:** one client owns a session and token, and token refresh mutates shared state.
5. **Version branching in one implementation:** server compatibility guards and namespace logic are distributed through clients instead of isolated behind adapters.
6. **Integration-test dependence:** tests cover operations against a live-like repository environment and require operational configuration.
7. **Duplicated package logic:** simple, complex, and generic package builders overlap in XIP construction and file-layout code.
8. **Limited formal async abstraction:** synchronous and asynchronous wrappers coexist with manual polling and process-token handling.

## 15. Evolution Recommendations

### Near term

- Split oversized modules into endpoint, model, package, and transport subpackages while preserving compatibility exports.
- Introduce a dedicated typed `PreservicaClient` façade over independently configured API clients.
- Centralize endpoint construction and response/exception handling in transport helpers.
- Expand automated unit tests with mock transport and XML fixtures, while retaining integration tests against a test tenancy.
- Replace `setup.py` with declarative `pyproject.toml` packaging and lock test/documentation dependencies.

### Medium term

- Introduce explicit retry policies per operation, distinguishing replay-safe reads from mutation retries.
- Move credential resolution behind a credential-provider protocol.
- Define stable public domain types and de-emphasize mutable XML-derived dictionaries.
- Separate package descriptors from ZIP/materialization and cloud-transfer implementations.
- Provide a typed async interface that can coexist with existing blocking/sync methods.

### Compatibility

For public API evolution, retain existing top-level exports and method names during deprecation periods. Preserve the existing `EntityAPI`, `ContentAPI`, `UploadAPI`, and package helper behavior unless a versioned compatibility layer is introduced.
