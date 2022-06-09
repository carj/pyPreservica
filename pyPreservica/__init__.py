"""
pyPreservica module definition
import API classes, for entity, content, upload, workflows & retention

author:     James Carr
licence:    Apache License 2.0

"""
from .common import *
from .contentAPI import ContentAPI
from .entityAPI import EntityAPI
from .uploadAPI import UploadAPI, simple_asset_package, complex_asset_package, cvs_to_xsd, cvs_to_xml, \
                    cvs_to_cmis_xslt, csv_to_search_xml, generic_asset_package, upload_config, multi_asset_package
from .workflowAPI import WorkflowAPI, WorkflowContext, WorkflowInstance
from .retentionAPI import RetentionAPI, RetentionAssignment, RetentionPolicy
from .parAPI import PreservationActionRegistry
from .adminAPI import AdminAPI


__author__ = "James Carr (drjamescarr@gmail.com)"

# Version of the Preservica API package
__version__ = "1.5.0"

__license__ = "Apache License Version 2.0"
