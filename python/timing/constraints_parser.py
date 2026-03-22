"""
Parse timing_constraints { ... } style blocks (semicolon-separated, brace-nested).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


def _strip_comments(s: str) -> str:
    return re.sub(r"//.*?$|/\*.*?\*/", "", s, flags=re.MULTILINE | re.DOTALL)


def _tokenize_block(inner: str) -> List[Tuple[str, str]]:
    """
    Split inner content into (key, value) where value may be a nested block {...}.
    """
    items: List[Tuple[str, str]] = []
    i = 0
    n = len(inner)
    while i < n:
        while i < n and inner[i] in " \t\n\r;":
            i += 1
        if i >= n:
            break
        m = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*", inner[i:])
        if not m:
            i += 1
            continue
        key = m.group(1)
        i += m.end()
        if i < n and inner[i] == "{":
            depth = 1
            j = i + 1
            while j < n and depth:
                if inner[j] == "{":
                    depth += 1
                elif inner[j] == "}":
                    depth -= 1
                j += 1
            val = inner[i + 1 : j - 1]
            items.append((key, "{" + val + "}"))
            i = j
        else:
            j = i
            while j < n and inner[j] not in ";":
                j += 1
            val = inner[i:j].strip()
            items.append((key, val))
            i = j + 1
    return items


def _parse_value_scalar(val: str) -> Any:
    val = val.strip().rstrip(";")
    if val.endswith("MHz") or val.endswith("mhz"):
        return val
    if val.endswith("ns"):
        return float(val.replace("ns", "").strip())
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def _parse_nested_block(block: str) -> Dict[str, Any]:
    inner = block.strip()
    if inner.startswith("{") and inner.endswith("}"):
        inner = inner[1:-1]
    out: Dict[str, Any] = {}
    for k, v in _tokenize_block(inner):
        if v.strip().startswith("{"):
            out[k] = _parse_nested_block(v)
        else:
            out[k] = _parse_value_scalar(v)
    return out


def parse_timing_constraints_text(text: str) -> Dict[str, Any]:
    """
    Parse a block starting with timing_constraints { ... }.

    Example::

        timing_constraints {
          tck_frequency_mhz: 200;
          system_clock_mhz: 400;
          setup_time_ns: 0.5;
          hold_time_ns: 0.3;
          propagation_delay_ns: 1.5;
          clock_domains {
            tclock: 200 MHz;
            sysclock: 400 MHz;
            ratio: 1:2;
            phase_offset: 0 ns;
          }
        }

    Returns a dict suitable for :func:`timing_config.load_timing_config_from_dict`.
    """
    s = _strip_comments(text)
    m = re.search(r"timing_constraints\s*\{", s, re.IGNORECASE)
    if not m:
        raise ValueError("No timing_constraints { block found")
    start = m.end() - 1
    depth = 0
    i = start
    while i < len(s):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                block = s[start : i + 1]
                inner = block[1:-1].strip()
                inner = re.sub(r"^\s*timing_constraints\s*", "", inner)
                flat: Dict[str, Any] = {}
                for k, v in _tokenize_block(inner):
                    if k == "timing_constraints":
                        continue
                    if v.strip().startswith("{"):
                        flat[k] = _parse_nested_block(v)
                    else:
                        flat[k] = _parse_value_scalar(v)
                if "clock_domains" in flat and isinstance(flat["clock_domains"], dict):
                    cd = flat["clock_domains"]
                    if "phase_offset" in cd and "phase_offset_ns" not in cd:
                        cd["phase_offset_ns"] = cd.pop("phase_offset")
                return flat
        i += 1
    raise ValueError("Unclosed timing_constraints block")
