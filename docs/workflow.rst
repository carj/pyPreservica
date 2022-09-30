Workflow API
~~~~~~~~~~~~~~

The workflow API allows clients to interact with the workflow engine, you can start workflows programmatically
and monitor the workflow queue etc.

.. note::
    The Workflow API is available for Enterprise Preservica users only


Begin by importing the pyPreservica module

.. code-block:: python

    from pyPreservica import *

Now, create the ``WorkflowAPI`` client

.. code-block:: python

    client = WorkflowAPI()

Fetching Workflow Contexts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The WorkflowAPI allows users to fetch a list of workflow contexts. A workflow context is a workflow definition
which has been configured and is ready to run.
Workflow contexts will appear in the "Manage" tab in the admin interface under the workflow type.

To fetch list of all workflow contexts by the workflow definition identifier

.. code-block:: python

    for workflow_context in client.get_workflow_contexts("com.preservica.core.workflow.ingest"):
        print(workflow_context.workflow_name)

To fetch a list of all workflow contexts by type:

The list of available types are:

* Ingest
* Access
* Transformation
* DataManagement

.. code-block:: python

    for workflow_context in client.get_workflow_contexts_by_type("Ingest"):
        print(workflow_context.workflow_name)


Fetching Workflow Instances
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A workflow instance is a workflow context which has been started and has either completed or is in progress.

Return a workflow instance by its identifier

.. code-block:: python

    workflow_instance = client.workflow_instance(instance_id)
    print(workflow_instance.workflow_context_name)
    print(workflow_instance.display_state)

Return a list of all Workflow instances, you can filter on workflow state and workflow type

Workflow States

* Aborted
* Active
* Completed
* Finished_Mixed_Outcome
* Pending
* Suspended
* Unknown
* Failed

Workflow Types

* Ingest
* Access
* Transformation
* DataManagement

.. code-block:: python

    for workflow_instance in client.workflow_instances("Completed", "Ingest"):
        print(workflow_instance)


Starting Workflows
^^^^^^^^^^^^^^^^^^^^^^

Once you have a workflow context setup, you can start workflows via the API.

To start the workflow pass a workflow context object as the argument

.. code-block:: python

    client.start_workflow_instance(workflow_context)


If a workflow requires additional arguments or you would like to override the defaults, you can pass
additional named arguments as additional parameters.

For example, to automatically start a new web crawl workflow, overriding some of the default parameters you
would use:

.. code-block:: python

    workflow_context = client.get_workflow_contexts("com.preservica.core.workflow.web.crawl.and.ingest")[0]

    client.start_workflow_instance(workflow_context, seedUrl="preservica.com", maxDepth="8", maxHops="10")
