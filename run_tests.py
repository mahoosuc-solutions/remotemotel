#!/usr/bin/env python3
"""
Test runner for hotel management system

This script runs all tests for the hotel management system.
"""

import sys
import os
import subprocess
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tests():
    """Run all tests for the hotel management system"""
    logger.info("Starting hotel management system tests...")
    
    # Test directories
    test_dirs = [
        "tests/unit/hotel",
        "tests/integration"
    ]
    
    # Test files
    test_files = [
        "tests/unit/hotel/test_models.py",
        "tests/unit/hotel/test_services.py", 
        "tests/unit/hotel/test_api.py",
        "tests/unit/hotel/test_voice_integration.py",
        "tests/integration/test_hotel_system.py"
    ]
    
    # Run pytest with coverage
    cmd = [
        "python", "-m", "pytest",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--cov=packages.hotel",  # Coverage for hotel package
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html:htmlcov",  # HTML coverage report
        "--cov-report=xml:coverage.xml",  # XML coverage report
        "--junitxml=test-results.xml",  # JUnit XML for CI
        "-x",  # Stop on first failure
    ]
    
    # Add test files
    cmd.extend(test_files)
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        logger.info("✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        logger.error("❌ pytest not found. Please install pytest: pip install pytest pytest-cov")
        return False

def run_specific_test(test_file):
    """Run a specific test file"""
    logger.info(f"Running specific test: {test_file}")
    
    cmd = [
        "python", "-m", "pytest",
        "-v",
        "--tb=short",
        test_file
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        logger.info(f"✅ Test {test_file} passed!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Test {test_file} failed with exit code {e.returncode}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        if not os.path.exists(test_file):
            logger.error(f"Test file not found: {test_file}")
            sys.exit(1)
        success = run_specific_test(test_file)
    else:
        # Run all tests
        success = run_tests()
    
    if success:
        logger.info("🎉 Test run completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Test run failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
