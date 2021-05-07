Preservation Action Registry API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyPreservica provides a python interface for using the Preservation Action Registry API

https://demo.preservica.com/Registry/par/documentation.html

For more information on PAR see: https://parcore.org/

This PyPreservica PAR client will work with any PAR implementation which uses HTTP Basic Auth.

Non-Authenticated Read Access
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The interfaces for reading information from the PAR are non-authenticated calls. Only a server address is
required. All the interfaces for reading information return JSON documents.

The JSON documents can be converted into Python Dictionaries using the standard json library.


* Format Families

.. code-block:: python

     import json

     par = PreservationActionRegistry(server="par-server.com")
     json_document = par.format_families()
     dict_obj = json.loads(json_document)

     json_document = par.format_family('ae87efa4-cd5a-5d07-b1b7-251a4fe871c8')
     dict_obj = json.loads(json_document)

* Preservation Action Types

.. code-block:: python

    par = PreservationActionRegistry(server="par-server.com")
    json_document = par.preservation_action_types()
    dict_obj = json.loads(json_document)


    json_document = par.preservation_action_type('ae87efa4-cd5a-5d07-b1b7-251a4fe871c8')
    dict_obj = json.loads(json_document)

* Properties

.. code-block:: python

     par = PreservationActionRegistry(server="par-server.com")
     json_document = par.properties()
     dict_obj = json.loads(json_document)

     json_document = par.property('ae87efa4-cd5a-5d07-b1b7-251a4fe871c8')
     dict_obj = json.loads(json_document)


* Representation Formats

.. code-block:: python

     par = PreservationActionRegistry(server="par-server.com")
     json_document = par.representation_format()
     dict_obj = json.loads(json_document)


     json_document = par.representation_formats('ae87efa4-cd5a-5d07-b1b7-251a4fe871c8')
     dict_obj = json.loads(json_document)


* File Formats

.. code-block:: python

    par = PreservationActionRegistry(server="par-server.com")
    json_document = par.file_formats()
    dict_obj = json.loads(json_document)


    json_document = par.file_format('ae87efa4-cd5a-5d07-b1b7-251a4fe871c8')
    dict_obj = json.loads(json_document)

* Tools

.. code-block:: python

     par = PreservationActionRegistry(server="par-server.com")
     json_document = par.tools()
     dict_obj = json.loads(json_document)


     json_document = par.tool('ae87efa4-cd5a-5d07-b1b7-251a4fe871c8')
     dict_obj = json.loads(json_document)

* Preservation Action

.. code-block:: python

     par = PreservationActionRegistry(server="par-server.com")
     json_document = par.preservation_actions()
     dict_obj = json.loads(json_document)


     json_document = par.preservation_action('ae87efa4-cd5a-5d07-b1b7-251a4fe871c8')
     dict_obj = json.loads(json_document)


* Business Rules

.. code-block:: python

     par = PreservationActionRegistry(server="par-server.com")
     json_document = par.business_rules()
     dict_obj = json.loads(json_document)


     json_document = par.business_rule('ae87efa4-cd5a-5d07-b1b7-251a4fe871c8')
     dict_obj = json.loads(json_document)



* Rule Sets

.. code-block:: python

    par = PreservationActionRegistry(server="par-server.com")
    json_document = par.rule_sets()
    dict_obj = json.loads(json_document)


    json_document = par.rule_set('ae87efa4-cd5a-5d07-b1b7-251a4fe871c8')
    dict_obj = json.loads(json_document)


