"""Allow running as python -m fault_coverage."""
from .fault_coverage_engine import _run_cli

if __name__ == "__main__":
    _run_cli()
