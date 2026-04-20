"""
GPU shader-core DFT specialization package.

Focuses on ALU, register file, and pipeline/interconnect verification with
functional, scan-based, and at-speed style checks.
"""

from .gpu_shader_verification import (
    GPUShaderConfig,
    GPUComprehensiveTest,
    GPUALUTest,
    GPURegisterFileTest,
    GPUPipelineTest,
    GPUFunctionalTest,
    parse_gpu_shader_config_text,
)
from .multi_core_verification import (
    MultiCoreGPUConfig,
    build_multi_core_report,
    parse_multi_core_config_text,
)

__all__ = [
    "GPUShaderConfig",
    "GPUComprehensiveTest",
    "GPUALUTest",
    "GPURegisterFileTest",
    "GPUPipelineTest",
    "GPUFunctionalTest",
    "parse_gpu_shader_config_text",
    "MultiCoreGPUConfig",
    "build_multi_core_report",
    "parse_multi_core_config_text",
]
