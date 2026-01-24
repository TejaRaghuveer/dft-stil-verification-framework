#!/usr/bin/env python3
"""
File Structure Validator
Validates project structure, file formats, and configuration files
for the DFT-STIL verification framework.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import json

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class FileStructureValidator:
    """
    Validates project directory structure and file organization.
    """
    
    REQUIRED_DIRS = [
        "uvm_tb/agents/jtag",
        "uvm_tb/agents/clock",
        "uvm_tb/agents/reset",
        "uvm_tb/agents/pad",
        "uvm_tb/env",
        "uvm_tb/sequences",
        "uvm_tb/tests",
        "uvm_tb/subscribers/stil",
        "uvm_tb/utils",
        "python/stil_generator",
        "python/atpg_parser",
        "python/validators",
        "python/utils",
        "config",
        "examples",
        "docs",
        "scripts"
    ]
    
    REQUIRED_FILES = [
        "README.md",
        "scripts/Makefile",
        "config/test_config.json"
    ]
    
    def __init__(self, project_root: str = "."):
        """
        Initialize validator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        
    def validate_directory_structure(self) -> Tuple[bool, List[str]]:
        """
        Validate that all required directories exist.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        for dir_path in self.REQUIRED_DIRS:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                errors.append(f"Missing directory: {dir_path}")
            elif not full_path.is_dir():
                errors.append(f"Path exists but is not a directory: {dir_path}")
                
        return len(errors) == 0, errors
        
    def validate_required_files(self) -> Tuple[bool, List[str]]:
        """
        Validate that all required files exist.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        for file_path in self.REQUIRED_FILES:
            full_path = self.project_root / file_path
            if not full_path.exists():
                errors.append(f"Missing file: {file_path}")
            elif not full_path.is_file():
                errors.append(f"Path exists but is not a file: {file_path}")
                
        return len(errors) == 0, errors
        
    def validate_stil_file(self, stil_file: str) -> Tuple[bool, List[str]]:
        """
        Validate STIL file format and syntax.
        
        Args:
            stil_file: Path to STIL file
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        stil_path = self.project_root / stil_file
        
        if not stil_path.exists():
            return False, [f"STIL file not found: {stil_file}"]
            
        with open(stil_path, 'r') as f:
            content = f.read()
            
        # Basic STIL syntax checks
        required_sections = ["STIL", "Signals"]
        for section in required_sections:
            if section not in content:
                errors.append(f"Missing required section: {section}")
                
        # Check for balanced braces
        if content.count('{') != content.count('}'):
            errors.append("Unbalanced braces in STIL file")
            
        return len(errors) == 0, errors
        
    def validate_config_file(self, config_file: str) -> Tuple[bool, List[str]]:
        """
        Validate configuration file format (JSON or YAML).
        
        Args:
            config_file: Path to config file
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        config_path = self.project_root / config_file
        
        if not config_path.exists():
            return False, [f"Config file not found: {config_file}"]
        
        try:
            with open(config_path, 'r') as f:
                if config_file.endswith('.json'):
                    json.load(f)
                elif config_file.endswith(('.yaml', '.yml')):
                    if HAS_YAML:
                        yaml.safe_load(f)
                    else:
                        errors.append(f"YAML support not available. Install pyyaml: pip install pyyaml")
                else:
                    errors.append(f"Unsupported config file format: {config_file}")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in config file: {e}")
        except Exception as e:
            errors.append(f"Error reading config file: {e}")
        
        return len(errors) == 0, errors
        
    def validate_all(self) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Run all validation checks.
        
        Returns:
            Tuple of (is_valid, dict_of_errors_by_category)
        """
        all_errors = {}
        
        # Validate directory structure
        dir_valid, dir_errors = self.validate_directory_structure()
        if not dir_valid:
            all_errors['directories'] = dir_errors
            
        # Validate required files
        file_valid, file_errors = self.validate_required_files()
        if not file_valid:
            all_errors['files'] = file_errors
            
        return len(all_errors) == 0, all_errors


def main():
    """Main validation entry point."""
    validator = FileStructureValidator()
    
    is_valid, errors = validator.validate_all()
    
    if is_valid:
        print("✓ Project structure validation passed")
        sys.exit(0)
    else:
        print("✗ Project structure validation failed:")
        for category, error_list in errors.items():
            print(f"\n{category.upper()}:")
            for error in error_list:
                print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
