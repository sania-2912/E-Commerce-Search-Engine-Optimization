"""
Backward-compatibility alias for Retrieval_Pipeline.models.model_loader
Directly maps to the real Retrieval_Pipeline module.
"""
import sys
import Retrieval_Pipeline.models.model_loader as _ml

sys.modules[__name__] = _ml
