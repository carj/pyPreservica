import uuid
from xml.dom import minidom
from xml.etree import ElementTree

from pyPreservica.common import *


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    re_parsed = minidom.parseString(rough_string)
    return re_parsed.toprettyxml(indent="  ")


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

    def __init__(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False):
        super().__init__(username, password, tenant, server, use_shared_secret)
        self.base_url = "sdb/rest/workflow"

    def get_workflow_contexts(self, definition: str):
        """
        Return a list of Workflow Contexts which have the same Workflow Definition ID

        :param definition: The Workflow Definition ID

        """
        headers = {HEADER_TOKEN: self.token}
        payload = {"workflowDefinitionId": definition}
        workflow_contexts = list()
        request = requests.get(f'https://{self.server}/{self.base_url}/contexts', headers=headers, params=payload)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            contexts = entity_response.findall(".//{*}WorkflowContext")
            for context in contexts:
                wrkfl_id = context.find(".//{*}Id").text
                name = context.find(".//{*}Name").text
                workflow_context = WorkflowContext(wrkfl_id, name)
                workflow_contexts.append(workflow_context)
            return workflow_contexts
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.get_workflow_contexts(definition)
        else:
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
            raise RuntimeError(request.status_code, "start_workflow_instance failed")
