#!/usr/bin/env python3
"""
ATPG Pattern Parser
Parses ATPG (Automatic Test Pattern Generation) output files and converts
them to STIL format or other test formats.

Supports common ATPG tool formats:
- Synopsys TetraMAX
- Mentor Graphics FastScan
- Cadence Encounter Test
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ATPGFormat(Enum):
    """Supported ATPG tool formats."""
    TETRAMAX = "tetramax"
    FASTSCAN = "fastscan"
    ENCOUNTER = "encounter"
    GENERIC = "generic"


@dataclass
class ATPGPattern:
    """Represents a parsed ATPG pattern."""
    pattern_id: str
    primary_inputs: Dict[str, str]  # pin_name -> value
    primary_outputs: Dict[str, str]  # pin_name -> expected_value
    scan_inputs: Dict[str, str]  # scan_chain -> value
    scan_outputs: Dict[str, str]  # scan_chain -> expected_value
    comment: Optional[str] = None


class ATPGParser:
    """
    Parser for ATPG tool output files.
    
    Converts ATPG patterns to internal representation that can be
    used for STIL generation or testbench stimulus.
    """
    
    def __init__(self, format_type: ATPGFormat = ATPGFormat.GENERIC):
        """
        Initialize ATPG parser.
        
        Args:
            format_type: Type of ATPG tool format to parse
        """
        self.format_type = format_type
        self.patterns: List[ATPGPattern] = []
        self.signals: List[str] = []
        
    def parse_tetramax(self, file_path: str):
        """
        Parse Synopsys TetraMAX ATPG output.
        
        Args:
            file_path: Path to TetraMAX output file
        """
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Extract patterns from TetraMAX format
        # Format: "pattern_name: pin1=value1 pin2=value2 ..."
        pattern_regex = r'(\w+):\s*((?:\w+=\w+\s*)+)'
        matches = re.finditer(pattern_regex, content)
        
        for match in matches:
            pattern_id = match.group(1)
            assignments = match.group(2).split()
            
            inputs = {}
            outputs = {}
            
            for assignment in assignments:
                if '=' in assignment:
                    pin, value = assignment.split('=', 1)  # Limit split to first '=' only
                    # Determine if input or output based on pin name convention
                    if pin.startswith('PO_') or pin.startswith('OUT_'):
                        outputs[pin] = value
                    else:
                        inputs[pin] = value
                        
            pattern = ATPGPattern(
                pattern_id=pattern_id,
                primary_inputs=inputs,
                primary_outputs=outputs,
                scan_inputs={},
                scan_outputs={}
            )
            self.patterns.append(pattern)
            
    def parse_fastscan(self, file_path: str):
        """
        Parse Mentor Graphics FastScan ATPG output.
        
        Args:
            file_path: Path to FastScan output file
        """
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        current_pattern = None
        in_pattern = False
        
        for line in lines:
            line = line.strip()
            
            # Pattern start
            if line.startswith('Pattern'):
                if current_pattern:
                    self.patterns.append(current_pattern)
                pattern_id = line.split()[1] if len(line.split()) > 1 else f"pattern_{len(self.patterns)}"
                current_pattern = ATPGPattern(
                    pattern_id=pattern_id,
                    primary_inputs={},
                    primary_outputs={},
                    scan_inputs={},
                    scan_outputs={}
                )
                in_pattern = True
                
            # Pin assignments
            elif in_pattern and '=' in line:
                parts = line.split('=')
                if len(parts) == 2:
                    pin = parts[0].strip()
                    value = parts[1].strip()
                    
                    # Categorize pins
                    if pin.startswith('SI_') or 'scan_in' in pin.lower():
                        current_pattern.scan_inputs[pin] = value
                    elif pin.startswith('SO_') or 'scan_out' in pin.lower():
                        current_pattern.scan_outputs[pin] = value
                    elif pin.startswith('PO_') or pin.startswith('OUT_'):
                        current_pattern.primary_outputs[pin] = value
                    else:
                        current_pattern.primary_inputs[pin] = value
                        
        if current_pattern:
            self.patterns.append(current_pattern)
            
    def parse_encounter(self, file_path: str):
        """
        Parse Cadence Encounter Test ATPG output.
        
        Args:
            file_path: Path to Encounter Test output file
        """
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Encounter Test format parsing
        # Look for vector definitions
        vector_regex = r'vector\s+(\w+)\s*\{([^}]+)\}'
        matches = re.finditer(vector_regex, content, re.MULTILINE)
        
        for match in matches:
            pattern_id = match.group(1)
            assignments = match.group(2)
            
            inputs = {}
            outputs = {}
            
            # Parse assignments
            assign_regex = r'(\w+)\s*=\s*([01XZ])'
            for assign_match in re.finditer(assign_regex, assignments):
                pin = assign_match.group(1)
                value = assign_match.group(2)
                
                if pin.startswith('PO_') or pin.startswith('OUT_'):
                    outputs[pin] = value
                else:
                    inputs[pin] = value
                    
            pattern = ATPGPattern(
                pattern_id=pattern_id,
                primary_inputs=inputs,
                primary_outputs=outputs,
                scan_inputs={},
                scan_outputs={}
            )
            self.patterns.append(pattern)
            
    def parse(self, file_path: str):
        """
        Parse ATPG file based on configured format.
        
        Args:
            file_path: Path to ATPG output file
        """
        if self.format_type == ATPGFormat.TETRAMAX:
            self.parse_tetramax(file_path)
        elif self.format_type == ATPGFormat.FASTSCAN:
            self.parse_fastscan(file_path)
        elif self.format_type == ATPGFormat.ENCOUNTER:
            self.parse_encounter(file_path)
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")
            
    def get_patterns(self) -> List[ATPGPattern]:
        """Get all parsed patterns."""
        return self.patterns
        
    def convert_to_stil_format(self) -> Dict:
        """
        Convert parsed patterns to STIL-compatible format.
        
        Returns:
            Dictionary with signals and patterns in STIL format
        """
        # Collect all signal names
        all_signals = set()
        for pattern in self.patterns:
            all_signals.update(pattern.primary_inputs.keys())
            all_signals.update(pattern.primary_outputs.keys())
            all_signals.update(pattern.scan_inputs.keys())
            all_signals.update(pattern.scan_outputs.keys())
            
        return {
            'signals': sorted(list(all_signals)),
            'patterns': self.patterns
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: atpg_parser.py <format> <input_file>")
        print("Formats: tetramax, fastscan, encounter")
        sys.exit(1)
        
    format_str = sys.argv[1].lower()
    input_file = sys.argv[2]
    
    format_map = {
        'tetramax': ATPGFormat.TETRAMAX,
        'fastscan': ATPGFormat.FASTSCAN,
        'encounter': ATPGFormat.ENCOUNTER
    }
    
    parser = ATPGParser(format_map.get(format_str, ATPGFormat.GENERIC))
    parser.parse(input_file)
    
    print(f"Parsed {len(parser.get_patterns())} patterns")
    for pattern in parser.get_patterns():
        print(f"  Pattern {pattern.pattern_id}: {len(pattern.primary_inputs)} inputs, {len(pattern.primary_outputs)} outputs")
