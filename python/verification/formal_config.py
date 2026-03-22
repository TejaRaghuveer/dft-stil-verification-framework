"""Parse formal_verification { ... } configuration blocks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List


def _strip_comments(s: str) -> str:
    return re.sub(r"//.*?$|/\*.*?\*/", "", s, flags=re.MULTILINE | re.DOTALL)


def parse_formal_verification_text(text: str) -> Dict[str, Any]:
    s = _strip_comments(text)
    m = re.search(r"formal_verification\s*\{", s, re.IGNORECASE)
    if not m:
        raise ValueError("No formal_verification { block found")
    start = m.end() - 1
    depth = 0
    i = start
    while i < len(s):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                inner = s[start + 1 : i]
                return _parse_inner(inner)
        i += 1
    raise ValueError("Unclosed formal_verification block")


def _parse_inner(inner: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    # key: value;  arrays like [a, b]
    for part in re.split(r";\s*\n?|\n(?=[a-z_]+\s*:)", inner):
        part = part.strip().rstrip(";").strip()
        if not part or part.startswith("//"):
            continue
        if ":" not in part:
            continue
        key, _, rest = part.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest.startswith("["):
            end = rest.rfind("]")
            arr = rest[1:end].replace(" ", "")
            out[key] = [x.strip() for x in arr.split(",") if x.strip()]
        elif rest.lower() in ("true", "false"):
            out[key] = rest.lower() == "true"
        else:
            try:
                if "." in rest:
                    out[key] = float(rest)
                else:
                    out[key] = int(rest)
            except ValueError:
                out[key] = rest.strip()
    return out


def load_formal_config_from_dict(d: Dict[str, Any]) -> "FormalVerificationConfig":
    return FormalVerificationConfig.from_dict(d)


def load_formal_config_from_yaml(path: str) -> "FormalVerificationConfig":
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise ImportError("pip install pyyaml for load_formal_config_from_yaml") from e
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    block = data.get("formal_verification", data)
    if not isinstance(block, dict):
        raise ValueError("Expected formal_verification mapping")
    return FormalVerificationConfig.from_dict(block)


@dataclass
class FormalVerificationConfig:
    enabled: bool = True
    proof_depth: int = 1000
    timeout_sec: int = 3600
    properties_to_prove: List[str] = field(default_factory=lambda: ["tap_fsm", "tdo_validity", "scan_path", "timing"])
    report_format: str = "JSON"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> FormalVerificationConfig:
        props = d.get("properties_to_prove") or d.get("properties", [])
        if isinstance(props, str):
            props = [p.strip() for p in props.strip("[]").split(",")]
        return cls(
            enabled=bool(d.get("enabled", True)),
            proof_depth=int(d.get("proof_depth", 1000)),
            timeout_sec=int(d.get("timeout", d.get("timeout_sec", 3600))),
            properties_to_prove=list(props),
            report_format=str(d.get("report_format", "JSON")),
        )
