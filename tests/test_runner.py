"""
EspoCRM Test Runner

Kapsamlı test suite runner ve raporlama.
"""

import pytest
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import coverage
import argparse


class TestRunner:
    """Test runner with advanced features."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = {}
        self.coverage_data = {}
        
    def run_tests(self, 
                  test_path: Optional[str] = None,
                  markers: Optional[List[str]] = None,
                  coverage_enabled: bool = True,
                  report_format: str = "console",
                  output_file: Optional[str] = None,
                  parallel: bool = False,
                  verbose: bool = False) -> Dict[str, Any]:
        """
        Run tests with specified options.
        
        Args:
            test_path: Specific test path to run
            markers: Test markers to include/exclude
            coverage_enabled: Enable coverage reporting
            report_format: Output format (console, json, html)
            output_file: Output file for reports
            parallel: Run tests in parallel
            verbose: Verbose output
            
        Returns:
            Test results dictionary
        """
        self.start_time = time.time()
        
        # Build pytest arguments
        args = self._build_pytest_args(
            test_path=test_path,
            markers=markers,
            coverage_enabled=coverage_enabled,
            parallel=parallel,
            verbose=verbose
        )
        
        # Start coverage if enabled
        cov = None
        if coverage_enabled:
            cov = coverage.Coverage(source=['espocrm'])
            cov.start()
        
        try:
            # Run pytest
            exit_code = pytest.main(args)
            
            # Stop coverage
            if cov:
                cov.stop()
                cov.save()
                
            self.end_time = time.time()
            
            # Collect results
            self.results = self._collect_results(exit_code, cov)
            
            # Generate reports
            self._generate_reports(report_format, output_file)
            
            return self.results
            
        except Exception as e:
            self.end_time = time.time()
            self.results = {
                "success": False,
                "error": str(e),
                "duration": self.end_time - self.start_time
            }
            return self.results
    
    def _build_pytest_args(self, 
                          test_path: Optional[str] = None,
                          markers: Optional[List[str]] = None,
                          coverage_enabled: bool = True,
                          parallel: bool = False,
                          verbose: bool = False) -> List[str]:
        """Build pytest command line arguments."""
        args = []
        
        # Test path
        if test_path:
            args.append(test_path)
        else:
            args.append("tests/")
        
        # Verbosity
        if verbose:
            args.extend(["-v", "-s"])
        
        # Markers
        if markers:
            for marker in markers:
                args.extend(["-m", marker])
        
        # Coverage
        if coverage_enabled:
            args.extend([
                "--cov=espocrm",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml"
            ])
        
        # Parallel execution
        if parallel:
            args.extend(["-n", "auto"])
        
        # Additional options
        args.extend([
            "--strict-markers",
            "--strict-config",
            "--tb=short"
        ])
        
        return args
    
    def _collect_results(self, exit_code: int, cov: Optional[coverage.Coverage]) -> Dict[str, Any]:
        """Collect test results and metrics."""
        results = {
            "success": exit_code == 0,
            "exit_code": exit_code,
            "duration": self.end_time - self.start_time,
            "timestamp": datetime.now().isoformat(),
            "coverage": {}
        }
        
        # Coverage data
        if cov:
            try:
                coverage_report = cov.report(show_missing=False)
                results["coverage"] = {
                    "total_statements": cov.get_data().measured_files(),
                    "covered_statements": coverage_report,
                    "percentage": round(coverage_report, 2) if coverage_report else 0
                }
                
                # Detailed coverage by module
                results["coverage"]["by_module"] = {}
                for filename in cov.get_data().measured_files():
                    analysis = cov.analysis2(filename)
                    if analysis:
                        module_name = self._get_module_name(filename)
                        results["coverage"]["by_module"][module_name] = {
                            "statements": len(analysis[1]),
                            "missing": len(analysis[3]),
                            "percentage": round(
                                (len(analysis[1]) - len(analysis[3])) / len(analysis[1]) * 100, 2
                            ) if analysis[1] else 0
                        }
                        
            except Exception as e:
                results["coverage"]["error"] = str(e)
        
        return results
    
    def _get_module_name(self, filename: str) -> str:
        """Convert filename to module name."""
        path = Path(filename)
        if "espocrm" in path.parts:
            espocrm_index = path.parts.index("espocrm")
            module_parts = path.parts[espocrm_index:]
            module_name = ".".join(module_parts).replace(".py", "")
            return module_name
        return filename
    
    def _generate_reports(self, format_type: str, output_file: Optional[str]):
        """Generate test reports."""
        if format_type == "json":
            self._generate_json_report(output_file)
        elif format_type == "html":
            self._generate_html_report(output_file)
        elif format_type == "console":
            self._generate_console_report()
    
    def _generate_json_report(self, output_file: Optional[str]):
        """Generate JSON report."""
        filename = output_file or "test_results.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"JSON report saved to: {filename}")
    
    def _generate_html_report(self, output_file: Optional[str]):
        """Generate HTML report."""
        filename = output_file or "test_results.html"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EspoCRM Test Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .success {{ color: green; }}
                .failure {{ color: red; }}
                .coverage {{ margin: 20px 0; }}
                .module {{ margin: 10px 0; padding: 10px; background: #f9f9f9; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>EspoCRM Test Results</h1>
                <p class="{'success' if self.results['success'] else 'failure'}">
                    Status: {'PASSED' if self.results['success'] else 'FAILED'}
                </p>
                <p>Duration: {self.results['duration']:.2f} seconds</p>
                <p>Timestamp: {self.results['timestamp']}</p>
            </div>
            
            <div class="coverage">
                <h2>Coverage Report</h2>
                <p>Total Coverage: {self.results.get('coverage', {}).get('percentage', 0)}%</p>
                
                <h3>Coverage by Module</h3>
                <table>
                    <tr>
                        <th>Module</th>
                        <th>Statements</th>
                        <th>Missing</th>
                        <th>Coverage %</th>
                    </tr>
        """
        
        for module, data in self.results.get('coverage', {}).get('by_module', {}).items():
            html_content += f"""
                    <tr>
                        <td>{module}</td>
                        <td>{data['statements']}</td>
                        <td>{data['missing']}</td>
                        <td>{data['percentage']}%</td>
                    </tr>
            """
        
        html_content += """
                </table>
            </div>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)
        print(f"HTML report saved to: {filename}")
    
    def _generate_console_report(self):
        """Generate console report."""
        print("\n" + "="*60)
        print("EspoCRM Test Results Summary")
        print("="*60)
        
        status = "PASSED" if self.results['success'] else "FAILED"
        print(f"Status: {status}")
        print(f"Duration: {self.results['duration']:.2f} seconds")
        print(f"Timestamp: {self.results['timestamp']}")
        
        if 'coverage' in self.results:
            coverage_pct = self.results['coverage'].get('percentage', 0)
            print(f"Coverage: {coverage_pct}%")
        
        print("="*60)


class TestSuiteManager:
    """Manage different test suites."""
    
    SUITES = {
        "unit": {
            "markers": ["unit"],
            "description": "Unit tests only"
        },
        "integration": {
            "markers": ["integration"],
            "description": "Integration tests only"
        },
        "auth": {
            "markers": ["auth"],
            "description": "Authentication tests"
        },
        "crud": {
            "markers": ["crud"],
            "description": "CRUD operation tests"
        },
        "metadata": {
            "markers": ["metadata"],
            "description": "Metadata tests"
        },
        "relationships": {
            "markers": ["relationships"],
            "description": "Relationship tests"
        },
        "stream": {
            "markers": ["stream"],
            "description": "Stream tests"
        },
        "attachments": {
            "markers": ["attachments"],
            "description": "Attachment tests"
        },
        "logging": {
            "markers": ["logging"],
            "description": "Logging tests"
        },
        "performance": {
            "markers": ["performance"],
            "description": "Performance tests"
        },
        "security": {
            "markers": ["security"],
            "description": "Security tests"
        },
        "slow": {
            "markers": ["slow"],
            "description": "Slow running tests"
        },
        "fast": {
            "markers": ["not slow"],
            "description": "Fast tests (exclude slow)"
        },
        "smoke": {
            "markers": ["unit", "not slow"],
            "description": "Smoke tests (fast unit tests)"
        },
        "full": {
            "markers": [],
            "description": "All tests"
        }
    }
    
    @classmethod
    def list_suites(cls):
        """List available test suites."""
        print("Available test suites:")
        print("-" * 40)
        for name, config in cls.SUITES.items():
            markers = ", ".join(config["markers"]) if config["markers"] else "all"
            print(f"{name:12} - {config['description']} (markers: {markers})")
    
    @classmethod
    def run_suite(cls, suite_name: str, **kwargs) -> Dict[str, Any]:
        """Run a specific test suite."""
        if suite_name not in cls.SUITES:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        suite_config = cls.SUITES[suite_name]
        runner = TestRunner()
        
        return runner.run_tests(
            markers=suite_config["markers"],
            **kwargs
        )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="EspoCRM Test Runner")
    
    parser.add_argument(
        "suite",
        nargs="?",
        default="fast",
        help="Test suite to run (use 'list' to see available suites)"
    )
    
    parser.add_argument(
        "--path",
        help="Specific test path to run"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    
    parser.add_argument(
        "--format",
        choices=["console", "json", "html"],
        default="console",
        help="Report format"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for reports"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--markers",
        nargs="+",
        help="Custom markers to run"
    )
    
    args = parser.parse_args()
    
    # List suites
    if args.suite == "list":
        TestSuiteManager.list_suites()
        return 0
    
    try:
        # Run custom markers or suite
        if args.markers:
            runner = TestRunner()
            results = runner.run_tests(
                test_path=args.path,
                markers=args.markers,
                coverage_enabled=not args.no_coverage,
                report_format=args.format,
                output_file=args.output,
                parallel=args.parallel,
                verbose=args.verbose
            )
        else:
            results = TestSuiteManager.run_suite(
                args.suite,
                test_path=args.path,
                coverage_enabled=not args.no_coverage,
                report_format=args.format,
                output_file=args.output,
                parallel=args.parallel,
                verbose=args.verbose
            )
        
        return 0 if results["success"] else 1
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())