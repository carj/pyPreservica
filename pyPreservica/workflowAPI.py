import uuid
import datetime
from xml.dom import minidom
from xml.etree import ElementTree

from pyPreservica.common import *

logger = logging.getLogger(__name__)


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    re_parsed = minidom.parseString(rough_string)
    return re_parsed.toprettyxml(indent="  ")


class WorkflowInstance:
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

    def __str__(self):
        return f"Workflow Instance ID: {self.instance_id}"

    def __repr__(self):
        return self.__str__()


class WorkflowContext:
    def __init__(self, workflow_id, workflow_name):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name

    def __str__(self):
        return f"Workflow ID:\t\t\t{self.workflow_id}\n" \
               f"Workflow Name:\t\t\t{self.workflow_name}\n"

    def __repr__(self):
        return self.__str__()


class WorkflowAPI(AuthenticatedAPI):
    """
              A client library for the Preservica Workflow API
              https://preview.preservica.com/sdb/rest/workflow/documentation.html

    """

    workflow_states = ['Aborted', 'Active', 'Completed', 'Finished_Mixed_Outcome', 'Pending', 'Suspended', 'Unknown',
                       'Failed']
    workflow_types = ['Ingest', 'Access', 'Transformation', 'DataManagement']

    def __init__(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False):
        super().__init__(username, password, tenant, server, use_shared_secret)
        self.base_url = "sdb/rest/workflow"

    def get_workflow_contexts_by_type(self, workflow_type: str):
        """
        Return a list of Workflow Contexts which have the same Workflow type

        :param workflow_type: The Workflow type:
        Ingest, Access, Transformation or DataManagement

        """
        headers = {HEADER_TOKEN: self.token}
        params = {"type": workflow_type}
        workflow_contexts = list()
        request = requests.get(f'https://{self.server}/{self.base_url}/contexts', headers=headers, params=params)
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
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.get_workflow_contexts(workflow_type)
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "get_workflow_contexts_by_type")

    def get_workflow_contexts(self, definition: str):
        """
        Return a list of Workflow Contexts which have the same Workflow Definition ID

        :param definition: The Workflow Definition ID

        """
        headers = {HEADER_TOKEN: self.token}
        params = {"workflowDefinitionId": definition}
        workflow_contexts = list()
        request = requests.get(f'https://{self.server}/{self.base_url}/contexts', headers=headers, params=params)
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
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.get_workflow_contexts(definition)
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "get_workflow_contexts")

    def start_workflow_instance(self, workflow_context, **kwargs):
        """

        Start a workflow context

        Returns a Correlation Id which is used to monitor the workflow progress

        :param workflow_context: The workflow context to start
        :param kwargs:           Key/Values to pass to the workflow instance

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
        request = requests.post(f'https://{self.server}/{self.base_url}/instances', headers=headers, data=xml_request)
        if request.status_code == requests.codes.created:
            return correlation_id
        if request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.start_workflow_instance(workflow_context, **kwargs)
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "start_workflow_instance failed")

    def terminate_workflow_instance(self, instance_ids):
        """
        Terminate a workflow by its instance id

        :param instance_ids: The Workflow instance:

        """
        if isinstance(instance_ids, list):
            converted_list = [str(int(e)) for e in instance_ids]
            param_string = ",".join(converted_list)
        else:
            param_string = str(int(instance_ids))

        headers = {HEADER_TOKEN: self.token}
        params = {"workflowInstanceIds": param_string}
        request = requests.post(f'https://{self.server}/{self.base_url}/instances/terminate',
                                headers=headers, params=params)
        if request.status_code == requests.codes.accepted:
            return
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.terminate_workflow_instance(instance_ids)
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "terminate_workflow_instance")

    def workflow_instance(self, instance_id: int):
        """
        Return a workflow instance by its Id

        :param instance_id: The Workflow instance:

        """
        headers = {HEADER_TOKEN: self.token}
        request = requests.get(f'https://{self.server}/{self.base_url}/instances/{str(instance_id)}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            w_id = int(entity_response.find(f".//{{{NS_WORKFLOW}}}Id").text)
            assert instance_id == w_id
            workflow_instance = WorkflowInstance(int(instance_id))
            started_element = entity_response.find(f".//{{{NS_WORKFLOW}}}Started")
            if started_element:
                if hasattr(started_element, "text"):
                    workflow_instance.started = datetime.datetime.strptime(started_element.text,
                                                                           '%Y-%m-%dT%H:%M:%S.%fZ')

            finished_element = entity_response.find(f".//{{{NS_WORKFLOW}}}Finished")
            if finished_element:
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

            return workflow_instance
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.workflow_instance(instance_id)
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "workflow_instance")

    def workflow_instances(self, workflow_state: str, workflow_type: str, **kwargs):
        """
        Return a list of Workflow instances

        :param workflow_state: The Workflow state: Aborted, Active, Completed, Finished_Mixed_Outcome, Pending, Suspended, Unknown, or Failed
        :param workflow_type: The Workflow type: Ingest, Access, Transformation or DataManagement

        """
        start_value = int(0)
        maximum = int(25)
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

        :param workflow_state: The Workflow state: Aborted, Active, Completed, Finished_Mixed_Outcome, Pending, Suspended, Unknown, or Failed
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

        if "from" in kwargs:
            from_date = kwargs.get("from")
            params["from"] = from_date

        if "to" in kwargs:
            to_date = kwargs.get("to")
            params["to"] = to_date

        params["start"] = int(start_value)
        params["max"] = int(maximum)

        request = requests.get(f'https://{self.server}/{self.base_url}/instances', headers=headers, params=params)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            total_count = int(entity_response.find(f".//{{{NS_WORKFLOW}}}TotalCount").text)
            count = int(entity_response.find(f".//{{{NS_WORKFLOW}}}Count").text)
            workflow_instance = entity_response.findall(f".//{{{NS_WORKFLOW}}}WorkflowInstance")
            workflow_instances = list()
            for instance in workflow_instance:
                instance_id = instance.find(f".//{{{NS_WORKFLOW}}}Id").text
                workflow_instance = WorkflowInstance(int(instance_id))

                started_element = instance.find(f".//{{{NS_WORKFLOW}}}Started")
                if started_element:
                    if hasattr(started_element, "text"):
                        workflow_instance.started = datetime.datetime.strptime(started_element.text,
                                                                               '%Y-%m-%dT%H:%M:%S.%fZ')

                finished_element = instance.find(f".//{{{NS_WORKFLOW}}}Finished")
                if finished_element:
                    if hasattr(finished_element, "text"):
                        workflow_instance.finished = datetime.datetime.strptime(finished_element.text,
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
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.__workflow_instances__(workflow_state, workflow_type, maximum, start_value, **kwargs)
        else:
            logger.error(request.content)
            raise RuntimeError(request.status_code, "workflow_instances")
