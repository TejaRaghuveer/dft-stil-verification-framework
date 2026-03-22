"""Multi-domain test execution: scheduling, TAM coordination, result aggregation."""

from .domain_manager import ExecutionMode, ResourceClaim, TestDomain, TestDomainManager
from .result_aggregator import DomainResult, MultiDomainResultAggregator
from .scheduler import DomainTestScheduler, ScheduledTest

__all__ = [
    "ExecutionMode",
    "ResourceClaim",
    "TestDomain",
    "TestDomainManager",
    "DomainTestScheduler",
    "ScheduledTest",
    "DomainResult",
    "MultiDomainResultAggregator",
]
