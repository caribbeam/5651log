#!/usr/bin/env python
"""
Test runner script for 5651log application
"""
import os
import sys
import subprocess
import django
from django.conf import settings
from django.test.utils import get_runner

def run_tests():
    """Run all tests with coverage"""
    print("🧪 Starting Test Coverage Analysis...")
    print("=" * 50)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yasalog.settings')
    django.setup()
    
    # Run tests with pytest
    try:
        # Run pytest with coverage
        result = subprocess.run([
            'python', '-m', 'pytest',
            'yasalog/',
            '--cov=yasalog',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-report=xml',
            '--cov-fail-under=80',
            '-v',
            '--tb=short'
        ], capture_output=True, text=True)
        
        print("📊 Test Results:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            print("📈 Coverage report generated in htmlcov/")
        else:
            print("❌ Some tests failed!")
            return False
            
    except FileNotFoundError:
        print("❌ pytest not found. Please install test dependencies:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def run_specific_tests(test_path):
    """Run specific test file or module"""
    print(f"🧪 Running specific tests: {test_path}")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            'python', '-m', 'pytest',
            test_path,
            '-v',
            '--tb=short'
        ], capture_output=True, text=True)
        
        print("📊 Test Results:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Warnings/Errors:")
            print(result.stderr)
            
    except FileNotFoundError:
        print("❌ pytest not found. Please install test dependencies:")
        print("pip install -r requirements.txt")
        return False
    
    return result.returncode == 0

def run_coverage_report():
    """Generate detailed coverage report"""
    print("📈 Generating detailed coverage report...")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            'python', '-m', 'coverage', 'report', '--show-missing'
        ], capture_output=True, text=True)
        
        print("📊 Coverage Report:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Warnings:")
            print(result.stderr)
            
    except FileNotFoundError:
        print("❌ coverage not found. Please install test dependencies:")
        print("pip install -r requirements.txt")
        return False
    
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--coverage':
            run_coverage_report()
        elif sys.argv[1] == '--specific':
            if len(sys.argv) > 2:
                run_specific_tests(sys.argv[2])
            else:
                print("❌ Please specify test path: python run_tests.py --specific yasalog/log_kayit/test_models.py")
        else:
            run_specific_tests(sys.argv[1])
    else:
        run_tests()
