#!/usr/bin/env python3
"""
Package Validation Script for EspoCRM Python Client

This script validates the package structure, imports, and metadata before release.
"""

import ast
import importlib.util
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class PackageValidator:
    """Package validation utility."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(f"❌ {message}")
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(f"⚠️  {message}")
    
    def add_info(self, message: str):
        """Add an info message."""
        self.info.append(f"ℹ️  {message}")
    
    def validate_file_structure(self) -> bool:
        """Validate package file structure."""
        print("🔍 Validating file structure...")
        
        required_files = [
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "CHANGELOG.md",
            "setup.py",
            "espocrm/__init__.py",
            "espocrm/py.typed",
        ]
        
        required_dirs = [
            "espocrm",
            "espocrm/auth",
            "espocrm/clients",
            "espocrm/models",
            "espocrm/utils",
            "espocrm/logging",
            "tests",
            "docs",
            "examples",
        ]
        
        # Check required files
        for file_path in required_files:
            full_path = PROJECT_ROOT / file_path
            if not full_path.exists():
                self.add_error(f"Missing required file: {file_path}")
            elif full_path.stat().st_size == 0:
                self.add_warning(f"Empty file: {file_path}")
            else:
                self.add_info(f"Found: {file_path}")
        
        # Check required directories
        for dir_path in required_dirs:
            full_path = PROJECT_ROOT / dir_path
            if not full_path.exists():
                self.add_error(f"Missing required directory: {dir_path}")
            elif not full_path.is_dir():
                self.add_error(f"Not a directory: {dir_path}")
            else:
                self.add_info(f"Found directory: {dir_path}")
        
        return len(self.errors) == 0
    
    def validate_imports(self) -> bool:
        """Validate that all imports work correctly."""
        print("🔍 Validating imports...")
        
        # Test main package import
        try:
            import espocrm
            self.add_info(f"Successfully imported espocrm v{espocrm.__version__}")
        except ImportError as e:
            self.add_error(f"Failed to import espocrm: {e}")
            return False
        
        # Test core imports
        core_imports = [
            "espocrm.EspoCRMClient",
            "espocrm.create_client",
            "espocrm.auth.APIKeyAuth",
            "espocrm.auth.BasicAuth",
            "espocrm.auth.HMACAuth",
            "espocrm.models.SearchParams",
            "espocrm.models.EntityRecord",
            "espocrm.exceptions.EspoCRMError",
            "espocrm.logging.get_logger",
        ]
        
        for import_path in core_imports:
            try:
                module_path, class_name = import_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                getattr(module, class_name)
                self.add_info(f"Successfully imported: {import_path}")
            except (ImportError, AttributeError) as e:
                self.add_error(f"Failed to import {import_path}: {e}")
        
        return len(self.errors) == 0
    
    def validate_syntax(self) -> bool:
        """Validate Python syntax in all Python files."""
        print("🔍 Validating Python syntax...")
        
        python_files = list(PROJECT_ROOT.glob("**/*.py"))
        syntax_errors = 0
        
        for py_file in python_files:
            # Skip __pycache__ and .git directories
            if "__pycache__" in str(py_file) or ".git" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                ast.parse(source, filename=str(py_file))
                
            except SyntaxError as e:
                self.add_error(f"Syntax error in {py_file}: {e}")
                syntax_errors += 1
            except UnicodeDecodeError as e:
                self.add_error(f"Encoding error in {py_file}: {e}")
                syntax_errors += 1
        
        if syntax_errors == 0:
            self.add_info(f"All {len(python_files)} Python files have valid syntax")
        
        return syntax_errors == 0
    
    def validate_metadata(self) -> bool:
        """Validate package metadata."""
        print("🔍 Validating package metadata...")
        
        # Check pyproject.toml
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        if not pyproject_path.exists():
            self.add_error("pyproject.toml not found")
            return False
        
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                self.add_warning("Cannot validate pyproject.toml - tomllib/tomli not available")
                return True
        
        try:
            with open(pyproject_path, 'rb') as f:
                pyproject_data = tomllib.load(f)
            
            # Validate required fields
            project = pyproject_data.get('project', {})
            required_fields = ['name', 'version', 'description', 'authors', 'license']
            
            for field in required_fields:
                if field not in project:
                    self.add_error(f"Missing required field in pyproject.toml: project.{field}")
                else:
                    self.add_info(f"Found metadata field: {field}")
            
            # Validate version format
            version = project.get('version', '')
            if not version:
                self.add_error("Version not specified in pyproject.toml")
            elif not self._is_valid_version(version):
                self.add_error(f"Invalid version format: {version}")
            else:
                self.add_info(f"Valid version: {version}")
            
            # Check dependencies
            dependencies = project.get('dependencies', [])
            if not dependencies:
                self.add_warning("No dependencies specified")
            else:
                self.add_info(f"Found {len(dependencies)} dependencies")
            
        except Exception as e:
            self.add_error(f"Error reading pyproject.toml: {e}")
            return False
        
        return len(self.errors) == 0
    
    def validate_entry_points(self) -> bool:
        """Validate entry points and CLI functionality."""
        print("🔍 Validating entry points...")
        
        # Check if CLI script exists
        cli_path = PROJECT_ROOT / "espocrm" / "cli.py"
        if not cli_path.exists():
            self.add_error("CLI module not found: espocrm/cli.py")
            return False
        
        # Test CLI import
        try:
            from espocrm.cli import main
            self.add_info("Successfully imported CLI main function")
        except ImportError as e:
            self.add_error(f"Failed to import CLI: {e}")
            return False
        
        # Test entry points in pyproject.toml
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                self.add_warning("Cannot validate entry points - tomllib/tomli not available")
                return True
        
        try:
            with open(PROJECT_ROOT / "pyproject.toml", 'rb') as f:
                pyproject_data = tomllib.load(f)
            
            scripts = pyproject_data.get('project', {}).get('scripts', {})
            if 'espocrm-cli' not in scripts:
                self.add_error("CLI entry point not found in pyproject.toml")
            else:
                self.add_info("Found CLI entry point: espocrm-cli")
            
        except Exception as e:
            self.add_error(f"Error validating entry points: {e}")
            return False
        
        return len(self.errors) == 0
    
    def validate_build(self) -> bool:
        """Validate that the package can be built."""
        print("🔍 Validating package build...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Build the package
                result = subprocess.run([
                    sys.executable, "-m", "build",
                    "--outdir", temp_dir,
                    str(PROJECT_ROOT)
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    self.add_error(f"Package build failed: {result.stderr}")
                    return False
                
                # Check if files were created
                dist_files = list(Path(temp_dir).glob("*"))
                if not dist_files:
                    self.add_error("No distribution files created")
                    return False
                
                wheel_files = [f for f in dist_files if f.suffix == ".whl"]
                tar_files = [f for f in dist_files if f.suffix == ".gz"]
                
                if not wheel_files:
                    self.add_error("No wheel file created")
                else:
                    self.add_info(f"Created wheel: {wheel_files[0].name}")
                
                if not tar_files:
                    self.add_error("No source distribution created")
                else:
                    self.add_info(f"Created source dist: {tar_files[0].name}")
                
                # Validate distributions with twine
                try:
                    result = subprocess.run([
                        sys.executable, "-m", "twine", "check"
                    ] + [str(f) for f in dist_files],
                    capture_output=True, text=True, timeout=60)
                    
                    if result.returncode != 0:
                        self.add_error(f"Distribution validation failed: {result.stderr}")
                    else:
                        self.add_info("Distribution files passed twine check")
                
                except FileNotFoundError:
                    self.add_warning("twine not available - skipping distribution validation")
                
            except subprocess.TimeoutExpired:
                self.add_error("Package build timed out")
                return False
            except Exception as e:
                self.add_error(f"Build validation failed: {e}")
                return False
        
        return len(self.errors) == 0
    
    def validate_installation(self) -> bool:
        """Validate that the package can be installed and imported."""
        print("🔍 Validating package installation...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Build the package first
                build_result = subprocess.run([
                    sys.executable, "-m", "build",
                    "--outdir", temp_dir,
                    str(PROJECT_ROOT)
                ], capture_output=True, text=True, timeout=300)
                
                if build_result.returncode != 0:
                    self.add_error("Cannot test installation - build failed")
                    return False
                
                # Find the wheel file
                wheel_files = list(Path(temp_dir).glob("*.whl"))
                if not wheel_files:
                    self.add_error("No wheel file found for installation test")
                    return False
                
                wheel_file = wheel_files[0]
                
                # Create a virtual environment for testing
                venv_dir = Path(temp_dir) / "test_venv"
                subprocess.run([
                    sys.executable, "-m", "venv", str(venv_dir)
                ], check=True, capture_output=True)
                
                # Determine the python executable in the venv
                if os.name == 'nt':  # Windows
                    venv_python = venv_dir / "Scripts" / "python.exe"
                else:  # Unix-like
                    venv_python = venv_dir / "bin" / "python"
                
                # Install the package
                install_result = subprocess.run([
                    str(venv_python), "-m", "pip", "install", str(wheel_file)
                ], capture_output=True, text=True, timeout=300)
                
                if install_result.returncode != 0:
                    self.add_error(f"Package installation failed: {install_result.stderr}")
                    return False
                
                # Test import
                import_result = subprocess.run([
                    str(venv_python), "-c",
                    "import espocrm; print(f'Successfully imported espocrm v{espocrm.__version__}')"
                ], capture_output=True, text=True, timeout=60)
                
                if import_result.returncode != 0:
                    self.add_error(f"Package import failed: {import_result.stderr}")
                    return False
                
                self.add_info("Package installation and import successful")
                
                # Test CLI
                cli_result = subprocess.run([
                    str(venv_python), "-m", "espocrm.cli", "--version"
                ], capture_output=True, text=True, timeout=60)
                
                if cli_result.returncode != 0:
                    self.add_warning(f"CLI test failed: {cli_result.stderr}")
                else:
                    self.add_info("CLI functionality working")
                
            except subprocess.TimeoutExpired:
                self.add_error("Installation test timed out")
                return False
            except Exception as e:
                self.add_error(f"Installation validation failed: {e}")
                return False
        
        return len(self.errors) == 0
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning."""
        import re
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9\-\.]+))?$'
        return bool(re.match(pattern, version))
    
    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print("🚀 Starting package validation...\n")
        
        validations = [
            ("File Structure", self.validate_file_structure),
            ("Python Syntax", self.validate_syntax),
            ("Package Metadata", self.validate_metadata),
            ("Import System", self.validate_imports),
            ("Entry Points", self.validate_entry_points),
            ("Package Build", self.validate_build),
            ("Installation", self.validate_installation),
        ]
        
        all_passed = True
        
        for name, validation_func in validations:
            print(f"\n{'='*50}")
            print(f"Validating: {name}")
            print('='*50)
            
            try:
                passed = validation_func()
                if not passed:
                    all_passed = False
                    print(f"❌ {name} validation FAILED")
                else:
                    print(f"✅ {name} validation PASSED")
            except Exception as e:
                self.add_error(f"Validation error in {name}: {e}")
                all_passed = False
                print(f"💥 {name} validation ERROR: {e}")
        
        return all_passed
    
    def print_summary(self):
        """Print validation summary."""
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print('='*60)
        
        if self.info:
            print(f"\n📋 Information ({len(self.info)} items):")
            for info in self.info:
                print(f"  {info}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)} items):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)} items):")
            for error in self.errors:
                print(f"  {error}")
        
        print(f"\n{'='*60}")
        if self.errors:
            print("❌ VALIDATION FAILED - Please fix the errors above")
            return False
        elif self.warnings:
            print("⚠️  VALIDATION PASSED WITH WARNINGS")
            return True
        else:
            print("✅ ALL VALIDATIONS PASSED - Package is ready for release!")
            return True


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate EspoCRM Python Client package",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip build validation (faster but less thorough)'
    )
    
    parser.add_argument(
        '--skip-install',
        action='store_true',
        help='Skip installation validation (faster but less thorough)'
    )
    
    parser.add_argument(
        '--json-output',
        help='Output results in JSON format to specified file'
    )
    
    args = parser.parse_args()
    
    validator = PackageValidator()
    
    # Skip certain validations if requested
    if args.skip_build:
        validator.validate_build = lambda: True
        validator.add_info("Skipped build validation")
    
    if args.skip_install:
        validator.validate_installation = lambda: True
        validator.add_info("Skipped installation validation")
    
    # Run validations
    success = validator.run_all_validations()
    
    # Print summary
    validator.print_summary()
    
    # JSON output if requested
    if args.json_output:
        results = {
            'success': success,
            'errors': validator.errors,
            'warnings': validator.warnings,
            'info': validator.info,
            'timestamp': str(datetime.now()),
        }
        
        with open(args.json_output, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {args.json_output}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()