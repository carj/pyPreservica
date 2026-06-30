"""
pyPreservica WorkflowAPI module definition

A client library for the Preservica Repository web services Workflow API
https://us.preservica.com/sdb/rest/workflow/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""

import uuid
import datetime
from typing import Callable, Generator
from xml.etree import ElementTree

from pyPreservica.common import *

logger = logging.getLogger(__name__)


class WorkflowInstance:
    """
        Defines a workflow Instance.
        The workflow Instance is a context which has been executed
    """

    def __init__(self, instance_id: int):
        self.instance_id = instance_id
        self.started = None
        self.finished = None
        self.state = None
        self.display_state = None
        self.archival_process_id = None
        self.workflow_group_id = None
        self.workflow_context_id = None
        self.workflow_context_name = None
        self.workflow_definition_id = None
        self.xml_response = None

    def __str__(self):
        return f"Workflow Instance ID: {self.instance_id}"

    def __repr__(self):
        return self.__str__()


class WorkflowContext:
    """
        Defines a workflow context.
        The workflow context is the pre-defined workflow which is ready to run
    """

    def __init__(self, workflow_id: str, workflow_name: str):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name

    def __str__(self):
        return f"""
              Workflow ID:    {self.workflow_id}
              Workflow Name:  {self.workflow_name}
        """

    def __repr__(self):
        return self.__str__()


class Process:
    """
    Defines an Ingest Process.
    """

    def __init__(self, process_id: str, process_name: str):
        self.process_id = process_id
        self.name = process_name
        self.description = ""
        self.type = None
        self.active: bool = False
        self.trigger_type = None

    def __str__(self):
        return f"""
              Process ID:           {self.process_id}
              Process Name:         {self.name}
              Process description:  {self.description}
              Process type:         {self.type}
              Process active:       {self.active}
              Process trigger type: {self.trigger_type}
        """

    def __repr__(self):
        return self.__str__()

class ProcessAPI(AuthenticatedAPI):
    """
    API for starting processes, and retrieving and updating configuration for processes.

    https://demo.preservica.com/api/process/documentation.html

    """

    def __init__(self, username: str|None = None, password: str|None = None, tenant: str|None = None, server: str|None = None,
                 use_shared_secret: bool = False, two_fa_secret_key: str|None = None,
                 protocol: str = "https", request_hook: Callable|None = None, credentials_path: str = 'credentials.properties'):

        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook, credentials_path)

        self.base_url = "api/process"



    def __set_status__(self, process_id: str, state: str) -> bool:

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json'}
        request = self.session.put(
            f'{self.protocol}://{self.server}/{self.base_url}/ingest/configs/{process_id}/active', headers=headers, data=str(state))
        if request.status_code == requests.codes.ok:
            config = json.loads(request.content.decode("utf-8"))
            return bool(config['active'])
        else:
            logger.error(request)
            raise RuntimeError(request.status_code, "deactivate_process")

    def deactivate_process(self, process_id: str) -> bool:
        """
        Deactivate an ingest process so that it no longer triggers ingests.

        :param process_id: The API id of the process to deactivate.
        :type process_id: str
        :returns: ``False`` reflecting the new active state of the process.
        :rtype: bool
        :raises RuntimeError: If the API call fails.
        """
        return self.__set_status__(process_id, 'false')

    def reactivate_process(self, process_id: str) -> bool:
        """
        Reactivate a previously deactivated ingest process.

        :param process_id: The API id of the process to reactivate.
        :type process_id: str
        :returns: ``True`` reflecting the new active state of the process.
        :rtype: bool
        :raises RuntimeError: If the API call fails.
        """
        return self.__set_status__(process_id, 'true')

    def ingest_process(self, ingest_types=None) -> list:
        """
        Return all configured ingest processes, optionally filtered by type.

        :param ingest_types: Optional type or list of types used to filter the results
            (e.g. ``"S3"``, ``"SFTP"``).  Pass ``None`` to return all processes.
        :type ingest_types: str or list or None
        :returns: List of :class:`Process` objects representing the configured ingest
            processes.
        :rtype: list[Process]
        """
        headers = {HEADER_TOKEN: self.token}
        params = {}
        if ingest_types is not None:
            params['types'] = ingest_types
        with self.session.get(f'{self.protocol}://{self.server}/{self.base_url}/ingest/configs', headers=headers, params=params)  as request:
            if request.status_code == requests.codes.ok:
                results = []
                json_dict = json.loads(request.content.decode("utf-8"))
                for entry in json_dict['configs']:
                    p = Process(entry['apiId'], entry['name'])
                    p.description = entry['description']
                    p.type = entry['type']
                    p.active = bool(entry['active'])
                    p.trigger_type = entry['trigger']['type']
                    results.append(p)
                return results
        return []

class WorkflowAPI(AuthenticatedAPI):
    """
        A class for calling the Preservica Workflow API

        This API can be used to programmatically manage the Preservica Workflows.

        https://demo.preservica.com/sdb/rest/workflow/documentation.html

    """

    workflow_states = ['Aborted', 'Active', 'Completed', 'Finished_Mixed_Outcome', 'Pending', 'Suspended', 'Unknown',
                       'Failed']
    workflow_types = ['Ingest', 'Access', 'Transformation', 'DataManagement']

    def __init__(self, username: str|None = None, password: str|None = None, tenant: str|None = None, server: str|None = None,
                 use_shared_secret: bool = False, two_fa_secret_key: str|None = None,
                 protocol: str = "https", request_hook: Callable|None = None, credentials_path: str = 'credentials.properties'):

        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook, credentials_path)
        self.base_url = "sdb/rest/workflow"

    def get_workflow_contexts_by_type(self, workflow_type: str) -> list[WorkflowContext]:
        """
        Return a list of Workflow Contexts that share the same workflow type.

        :param workflow_type: The workflow type to filter by. Must be one of
            ``"Ingest"``, ``"Access"``, ``"Transformation"``, or ``"DataManagement"``.
        :type workflow_type: str
        :returns: List of :class:`WorkflowContext` objects whose type matches
            ``workflow_type``.
        :rtype: list[WorkflowContext]
        :raises RuntimeError: If the API call fails.
        """

        headers = {HEADER_TOKEN: self.token}
        params = {"type": workflow_type}
        workflow_contexts: list[WorkflowContext] = []
        request = self.session.get(f'{self.protocol}://{self.server}/{self.base_url}/contexts', headers=headers, params=params)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            contexts = entity_response.findall(f".//{{{NS_WORKFLOW}}}WorkflowContext")
            for context in contexts:
                workflow_element_id = context.find(f".//{{{NS_WORKFLOW}}}Id")
                workflow_id = workflow_element_id.text if workflow_element_id is not None else None
                workflow_element_name = context.find(f".//{{{NS_WORKFLOW}}}Name")
                name = workflow_element_name.text if workflow_element_name is not None else None
                if workflow_id is not None and name is not None:
                    workflow_context = WorkflowContext(workflow_id, name)
                    workflow_contexts.append(workflow_context)
            return workflow_contexts
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "get_workflow_contexts_by_type")

    def get_workflow_contexts(self, definition: str) -> list[WorkflowContext]:
        """
        Return a list of Workflow Contexts that share the same Workflow Definition.

        :param definition: The Workflow Definition text ID used to filter contexts.
        :type definition: str
        :returns: List of :class:`WorkflowContext` objects associated with the given
            workflow definition.
        :rtype: list[WorkflowContext]
        :raises RuntimeError: If the API call fails.
        """

        headers = {HEADER_TOKEN: self.token}
        params = {"workflowDefinitionId": definition}
        workflow_contexts: list[WorkflowContext] = []
        request = self.session.get(f'{self.protocol}://{self.server}/{self.base_url}/contexts', headers=headers, params=params)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            contexts = entity_response.findall(f".//{{{NS_WORKFLOW}}}WorkflowContext")
            for context in contexts:
                wrkfl_id = context.find(f".//{{{NS_WORKFLOW}}}Id").text
                name = context.find(f".//{{{NS_WORKFLOW}}}Name").text
                workflow_context = WorkflowContext(wrkfl_id, name)
                workflow_contexts.append(workflow_context)
            return workflow_contexts
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "get_workflow_contexts")

    def start_workflow_instance(self, workflow_context: WorkflowContext, **kwargs):
        """
        Start a new workflow instance from the given workflow context.

        Any extra keyword arguments are forwarded to the workflow as ``Key``/``Value``
        parameter pairs in the XML start request (e.g. ``parameter_key=parameter_value``).

        :param workflow_context: The workflow context to start.
        :type workflow_context: WorkflowContext
        :param kwargs: Arbitrary keyword arguments forwarded as workflow parameters.
        :returns: A UUID correlation id that can be used to monitor the workflow progress.
        :rtype: str
        :raises RuntimeError: If the server does not return HTTP 201 Created.
        """

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        correlation_id = str(uuid.uuid4())

        request_payload = xml.etree.ElementTree.Element('StartWorkflowRequest ',
                                                        {"xmlns": "http://workflow.preservica.com"})
        xml.etree.ElementTree.SubElement(request_payload, "WorkflowContextId").text = workflow_context.workflow_id
        xml.etree.ElementTree.SubElement(request_payload, "WorkflowContextName").text = workflow_context.workflow_name

        for key, value in kwargs.items():
            parameter = xml.etree.ElementTree.SubElement(request_payload, "Parameter")
            xml.etree.ElementTree.SubElement(parameter, "Key").text = key
            xml.etree.ElementTree.SubElement(parameter, "Value").text = value

        xml.etree.ElementTree.SubElement(request_payload, "CorrelationId").text = correlation_id

        xml_request = xml.etree.ElementTree.tostring(request_payload, encoding='utf-8')
        request = self.session.post(f'{self.protocol}://{self.server}/{self.base_url}/instances', headers=headers,
                                    data=xml_request)
        if request.status_code == requests.codes.created:
            return correlation_id
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "start_workflow_instance failed")

    def terminate_workflow_instance(self, instance_ids):
        """
        Terminate one or more running workflow instances by their instance ids.

        :param instance_ids: A single workflow instance id or a list of instance ids to
            terminate.
        :type instance_ids: int or list[int]
        :returns: None
        :rtype: None
        :raises RuntimeError: If the server does not return HTTP 202 Accepted.
        """

        if isinstance(instance_ids, list):
            converted_list = [str(int(e)) for e in instance_ids]
            param_string = ",".join(converted_list)
        else:
            param_string = str(int(instance_ids))

        headers = {HEADER_TOKEN: self.token}
        params = {"workflowInstanceIds": param_string}
        request = self.session.post(f'{self.protocol}://{self.server}/{self.base_url}/instances/terminate',
                                    headers=headers, params=params)
        if request.status_code == requests.codes.accepted:
            return
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "terminate_workflow_instance")

    def workflow_instance(self, instance_id: int) -> WorkflowInstance:
        """
        Retrieve a single workflow instance by its numeric id.

        The returned :class:`WorkflowInstance` is populated with state, timing, context,
        and archival process information retrieved from the server.

        :param instance_id: The numeric id of the workflow instance to retrieve.
        :type instance_id: int
        :returns: A fully populated :class:`WorkflowInstance` object.
        :rtype: WorkflowInstance
        :raises RuntimeError: If the server returns a non-200 response.
        """

        headers = {HEADER_TOKEN: self.token}
        params = {"includeErrors": "true"}
        request = self.session.get(f'{self.protocol}://{self.server}/{self.base_url}/instances/{str(instance_id)}',
                                   headers=headers, params=params)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            w_id = int(entity_response.find(f".//{{{NS_WORKFLOW}}}Id").text)
            assert instance_id == w_id
            workflow_instance = WorkflowInstance(int(instance_id))
            started_element = entity_response.find(f".//{{{NS_WORKFLOW}}}Started")
            if started_element is not None:
                if hasattr(started_element, "text"):
                    workflow_instance.started = datetime.datetime.strptime(started_element.text,
                                                                           '%Y-%m-%dT%H:%M:%S.%fZ')

            finished_element = entity_response.find(f".//{{{NS_WORKFLOW}}}Finished")
            if finished_element is not None:
                if hasattr(finished_element, "text"):
                    workflow_instance.finished = datetime.datetime.strptime(finished_element.text,
                                                                            '%Y-%m-%dT%H:%M:%S.%fZ')

            workflow_instance.state = entity_response.find(f".//{{{NS_WORKFLOW}}}State").text
            workflow_instance.display_state = entity_response.find(f".//{{{NS_WORKFLOW}}}DisplayState").text
            workflow_instance.archival_process_id = entity_response.find(f".//{{{NS_WORKFLOW}}}ArchivalProcessId").text
            workflow_instance.workflow_group_id = entity_response.find(f".//{{{NS_WORKFLOW}}}WorkflowGroupId").text
            workflow_instance.workflow_context_id = entity_response.find(f".//{{{NS_WORKFLOW}}}WorkflowContextId").text
            workflow_instance.workflow_context_name = entity_response.find(
                f".//{{{NS_WORKFLOW}}}WorkflowContextName").text
            workflow_instance.workflow_definition_id = entity_response.find(
                f".//{{{NS_WORKFLOW}}}WorkflowDefinitionTextId").text

            workflow_instance.xml_response = xml_response

            return workflow_instance
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "workflow_instance")

    def workflow_instances(self, workflow_state: str, workflow_type: str, **kwargs) -> Generator[WorkflowInstance, None, None]:
        """
        Return a generator of workflow instances filtered by state and type.

        Results are fetched from the server in pages of 100 and yielded lazily.
        Optional keyword arguments allow further filtering by context, creator, or date
        range.

        :param workflow_state: The workflow state to filter by. Must be one of
            ``"Aborted"``, ``"Active"``, ``"Completed"``, ``"Finished_Mixed_Outcome"``,
            ``"Pending"``, ``"Suspended"``, ``"Unknown"``, or ``"Failed"``.
        :type workflow_state: str
        :param workflow_type: The workflow type to filter by. Must be one of
            ``"Ingest"``, ``"Access"``, ``"Transformation"``, or ``"DataManagement"``.
        :type workflow_type: str
        :param contextId: Optional workflow context id to filter results.
        :type contextId: str
        :param creator: Optional username of the workflow creator to filter results.
        :type creator: str
        :param from_date: Optional start date for filtering by workflow start time.
        :type from_date: datetime.date or datetime.datetime or str
        :param to_date: Optional end date for filtering by workflow start time.
        :type to_date: datetime.date or datetime.datetime or str
        :returns: Generator that lazily yields :class:`WorkflowInstance` objects.
        :rtype: Generator[WorkflowInstance, None, None]
        :raises RuntimeError: If an invalid state or type is supplied, or if the API
            call fails.
        """

        start_value = int(0)
        maximum = int(100)
        total_count = maximum
        while total_count > start_value:
            result = self.__workflow_instances__(workflow_state, workflow_type, maximum=maximum,
                                                 start_value=start_value, **kwargs)
            workflow_instances_list = result[2]
            total_count = result[0]
            start_value = start_value + result[1]
            for w in workflow_instances_list:
                yield w

    def __workflow_instances__(self, workflow_state: str, workflow_type: str, maximum: int = 25, start_value: int = 0,
                               **kwargs):
        """
        Return a list of Workflow instances

        :param workflow_state: The Workflow state: Aborted, Active, Completed, Finished_Mixed_Outcome, Pending,
        Suspended, Unknown, or Failed
        :param workflow_type: The Workflow type: Ingest, Access, Transformation or DataManagement

        """

        headers = {HEADER_TOKEN: self.token}

        if workflow_state not in self.workflow_states:
            logger.error("Invalid Workflow State")
            raise RuntimeError("Invalid Workflow State")

        if workflow_type not in self.workflow_types:
            logger.error("Invalid Workflow Type")
            raise RuntimeError("Invalid Workflow Type")

        params = {"type": workflow_type, "state": workflow_state}

        if "contextId" in kwargs:
            context_id = kwargs.get("contextId")
            params["contextId"] = context_id

        if "creator" in kwargs:
            creator = kwargs.get("creator")
            params["creator"] = creator

        if "from_date" in kwargs:
            from_date = kwargs.get("from_date")
            params["from"] = parse_date_to_iso(from_date)

        if "to_date" in kwargs:
            to_date = kwargs.get("to_date")
            params["to"] = parse_date_to_iso(to_date)

        params["start"] = int(start_value)
        params["max"] = int(maximum)

        request = self.session.get(f'{self.protocol}://{self.server}/{self.base_url}/instances', headers=headers, params=params)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            total_count = int(entity_response.find(f".//{{{NS_WORKFLOW}}}TotalCount").text)
            count = int(entity_response.find(f".//{{{NS_WORKFLOW}}}Count").text)
            workflow_instance = entity_response.findall(f".//{{{NS_WORKFLOW}}}WorkflowInstance")
            workflow_instances = []
            for instance in workflow_instance:
                instance_id = instance.find(f".//{{{NS_WORKFLOW}}}Id").text
                workflow_instance = WorkflowInstance(int(instance_id))

                started_element = instance.find(f".//{{{NS_WORKFLOW}}}Started")
                if started_element is not None:
                    if hasattr(started_element, "text"):
                        workflow_instance.started = time.strptime(started_element.text,
                                                                               '%Y-%m-%dT%H:%M:%S.%fZ')

                finished_element = instance.find(f".//{{{NS_WORKFLOW}}}Finished")
                if finished_element is not None:
                    if hasattr(finished_element, "text"):
                        workflow_instance.finished = time.strptime(finished_element.text,
                                                                                '%Y-%m-%dT%H:%M:%S.%fZ')

                workflow_instance.state = instance.find(f".//{{{NS_WORKFLOW}}}State").text
                workflow_instance.display_state = instance.find(f".//{{{NS_WORKFLOW}}}DisplayState").text
                workflow_instance.archival_process_id = instance.find(f".//{{{NS_WORKFLOW}}}ArchivalProcessId").text
                workflow_instance.workflow_group_id = instance.find(f".//{{{NS_WORKFLOW}}}WorkflowGroupId").text
                workflow_instance.workflow_context_id = instance.find(f".//{{{NS_WORKFLOW}}}WorkflowContextId").text
                workflow_instance.workflow_context_name = instance.find(f".//{{{NS_WORKFLOW}}}WorkflowContextName").text
                workflow_instance.workflow_definition_id = instance.find(
                    f".//{{{NS_WORKFLOW}}}WorkflowDefinitionTextId").text
                workflow_instances.append(workflow_instance)
            return tuple((total_count, count, workflow_instances))
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "workflow_instances")

