"""
Backward-compatibility alias for Retrieval_Pipeline.retrieval_pipeline
Directly maps to the real Retrieval_Pipeline module.
"""
import sys
import Retrieval_Pipeline.retrieval_pipeline as _rp

sys.modules[__name__] = _rp
