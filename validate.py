#!/usr/bin/env python3
"""
Validation script to check project structure and basic imports
"""
import os
import sys
from pathlib import Path

def check_structure():
    """Check if all required directories exist"""
    print("Checking project structure...")
    
    required_dirs = [
        'src/ingestion',
        'src/processing',
        'src/storage',
        'src/models',
        'src/orchestration',
        'src/utils',
        'dashboards',
        'config',
        'tests',
        'data/raw',
        'data/processed',
        'data/models',
        'docs'
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing.append(dir_path)
    
    if missing:
        print(f"❌ Missing directories: {missing}")
        return False
    else:
        print("✅ All required directories exist")
        return True


def check_files():
    """Check if all required files exist"""
    print("\nChecking required files...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'setup.sh',
        'README.md',
        '.gitignore',
        'config/config.yaml',
        'config/.env.template',
        'src/ingestion/kafka_producer.py',
        'src/ingestion/kafka_consumer.py',
        'src/ingestion/api_client.py',
        'src/processing/stream_processor.py',
        'src/processing/feature_engineering.py',
        'src/storage/connectors.py',
        'src/models/loan_default_model.py',
        'src/orchestration/loan_risk_dag.py',
        'dashboards/risk_dashboard.py',
        'tests/test_feature_engineering.py',
        'tests/test_model.py'
    ]
    
    missing = []
    for file_path in required_files:
        if not os.path.isfile(file_path):
            missing.append(file_path)
    
    if missing:
        print(f"❌ Missing files: {missing}")
        return False
    else:
        print("✅ All required files exist")
        return True


def check_python_version():
    """Check Python version"""
    print("\nChecking Python version...")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (Need 3.8+)")
        return False


def count_components():
    """Count project components"""
    print("\nCounting components...")
    
    py_files = len(list(Path('src').rglob('*.py')))
    test_files = len(list(Path('tests').rglob('*.py')))
    
    print(f"📊 Python modules in src/: {py_files}")
    print(f"📊 Test files: {test_files}")
    print(f"📊 Configuration files: {len(list(Path('config').rglob('*.*')))}")
    print(f"📊 Documentation files: {len(list(Path('docs').rglob('*.md')))}")


def main():
    """Run all validation checks"""
    print("=" * 60)
    print("Real-Time Loan Default Risk Pipeline - Structure Validation")
    print("=" * 60)
    
    checks = [
        check_python_version(),
        check_structure(),
        check_files()
    ]
    
    count_components()
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All validation checks passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure credentials: cp config/.env.template config/.env")
        print("3. Start services: docker-compose up -d")
        print("4. Run pipeline: python main.py --mode full")
        return 0
    else:
        print("❌ Some validation checks failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
