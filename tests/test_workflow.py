import pytest
from pyPreservica import *


def test_get_workflow_contexts():
    workflow = WorkflowAPI()
    workflows = workflow.get_workflow_contexts("com.preservica.core.workflow.ingest.single.file")
    assert len(workflows) == 1


def test_get_workflow_contexts2():
    workflow = WorkflowAPI()
    workflows = workflow.get_workflow_contexts("com.preservica.core.workflow.ingest")
    assert len(workflows) == 1


def test_get_workflow_contexts3():
    workflow = WorkflowAPI()
    workflows = workflow.get_workflow_contexts("com.preservica.core.workflow.delete")
    assert len(workflows) == 1


def test_get_workflow_contexts_type():
    workflow = WorkflowAPI()

    workflows = workflow.get_workflow_contexts_by_type("Ingest")
    assert len(workflows) == 6

    workflows = workflow.get_workflow_contexts_by_type("Access")
    assert len(workflows) == 5

    workflows = workflow.get_workflow_contexts_by_type("Transformation")
    assert len(workflows) == 2

    workflows = workflow.get_workflow_contexts_by_type("DataManagement")
    assert len(workflows) == 20

