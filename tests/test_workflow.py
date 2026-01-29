import pytest
from pyPreservica import *


def test_get_workflow_contexts():
    workflow = WorkflowAPI()
    workflows = workflow.get_workflow_contexts("com.preservica.core.workflow.ingest.single.file")
    assert len(workflows) == 1


def test_get_workflow_contexts2():
    workflow = WorkflowAPI()
    workflows = workflow.get_workflow_contexts("com.preservica.core.workflow.ingest")
    assert len(workflows) > 1


def test_get_workflow_contexts3():
    workflow = WorkflowAPI()
    workflows = workflow.get_workflow_contexts("com.preservica.core.workflow.delete")
    assert len(workflows) == 1


def test_get_workflow_contexts_type():
    workflow = WorkflowAPI()

    workflows = workflow.get_workflow_contexts_by_type("Ingest")
    assert len(workflows) == 9

    workflows = workflow.get_workflow_contexts_by_type("Access")
    assert len(workflows) == 3

    workflows = workflow.get_workflow_contexts_by_type("Transformation")
    assert len(workflows) == 2

    workflows = workflow.get_workflow_contexts_by_type("DataManagement")
    assert len(workflows) == 22



def test_get_workflow_instances():
    workflow = WorkflowAPI()
    assert len(list(workflow.workflow_instances(workflow_state="Completed", workflow_type="Ingest",  from_date="2025-01-01", to_date="2026-01-01"))) == 423

    assert len(list(workflow.workflow_instances(workflow_state="Aborted", workflow_type="Ingest",  from_date="2025-01-01", to_date="2026-01-01"))) == 9
