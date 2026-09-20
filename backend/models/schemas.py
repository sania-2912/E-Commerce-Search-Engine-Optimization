"""
Backward-compatibility alias for Retrieval_Pipeline.models.schemas
Directly maps to the real Retrieval_Pipeline module.
"""
import sys
import Retrieval_Pipeline.models.schemas as _schemas

sys.modules[__name__] = _schemas
