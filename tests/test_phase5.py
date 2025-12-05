import pytest
import sys
import os
sys.path.append(os.getcwd())

from datetime import datetime, timezone


def test_report_module_exists():
    """Test 5.1: Report generation module exists and has required functions"""
    from reports import generate_report
    
    # Check key functions exist
    assert hasattr(generate_report, 'get_transaction_statistics')
    assert hasattr(generate_report, 'get_fraud_statistics')
    assert hasattr(generate_report, 'get_validation_statistics')
    assert hasattr(generate_report, 'get_system_performance')
    assert hasattr(generate_report, 'generate_console_report')
    assert hasattr(generate_report, 'save_report_json')
    
    print("✓ Test 5.1 PASSED: Report module structure is complete")


def test_readme_documentation():
    """Test 5.2: README contains comprehensive documentation"""
    with open('README.md', 'r') as f:
        readme = f.read()
    
    # Check key sections
    required_sections = [
        'FinTech Fraud Detection',
        'Architecture',
        'Lambda Architecture',
        'Kafka',
        'Spark',
        'PostgreSQL',
        'Airflow',
        'Installation',
        'Usage',
        'Testing'
    ]
    
    for section in required_sections:
        assert section in readme, f"README missing section: {section}"
    
    print(f"✓ Test 5.2 PASSED: README contains {len(required_sections)} required sections")


def test_project_structure_completeness():
    """Test 5.3: All project directories and key files exist"""
    required_paths = [
        'database/init.sql',
        'database/db_config.py',
        'kafka_client/config.py',
        'kafka_client/producer.py',
        'spark/fraud_detection_streaming.py',
        'spark/spark_config.py',
        'airflow/dags/etl_reconciliation_dag.py',
        'reports/generate_report.py',
        'docker-compose.yml',
        'requirements.txt',
        '.gitignore',
        'TODO.md'
    ]
    
    missing = []
    for path in required_paths:
        if not os.path.exists(path):
            missing.append(path)
    
    assert len(missing) == 0, f"Missing files: {missing}"
    
    print(f"✓ Test 5.3 PASSED: All {len(required_paths)} required project files exist")


def test_all_phase_tests_exist():
    """Test 5.4: Test files for all phases exist"""
    test_files = [
        'tests/test_phase1.py',
        'tests/test_phase2.py',
        'tests/test_phase3.py',
        'tests/test_phase4.py',
        'tests/test_phase5.py'
    ]
    
    for test_file in test_files:
        assert os.path.exists(test_file), f"Test file missing: {test_file}"
    
    print(f"✓ Test 5.4 PASSED: All {len(test_files)} phase test files exist")


def test_docker_compose_services():
    """Test 5.5: Docker Compose defines all required services"""
    with open('docker-compose.yml', 'r') as f:
        compose = f.read()
    
    required_services = [
        'zookeeper',
        'kafka',
        'postgres',
        'airflow'
    ]
    
    for service in required_services:
        assert service in compose, f"Docker Compose missing service: {service}"
    
    print(f"✓ Test 5.5 PASSED: Docker Compose defines {len(required_services)} required services")


def test_requirements_dependencies():
    """Test 5.6: requirements.txt contains all necessary dependencies"""
    with open('requirements.txt', 'r') as f:
        requirements = f.read().lower()  # Case-insensitive check
    
    required_packages = [
        'kafka-python',
        'pyspark',
        'psycopg2-binary',
        'apache-airflow',
        'pandas',
        'faker',
        'pytest'
    ]
    
    for package in required_packages:
        assert package in requirements, f"requirements.txt missing: {package}"
    
    print(f"✓ Test 5.6 PASSED: All {len(required_packages)} required packages in requirements.txt")


def test_gitignore_configuration():
    """Test 5.7: .gitignore properly configured"""
    with open('.gitignore', 'r') as f:
        gitignore = f.read()
    
    required_ignores = [
        '.venv',
        '__pycache__',
        '*.pyc',
        '.pytest_cache'
    ]
    
    for pattern in required_ignores:
        assert pattern in gitignore, f".gitignore missing pattern: {pattern}"
    
    print(f"✓ Test 5.7 PASSED: .gitignore properly configured with {len(required_ignores)} patterns")


def test_todo_completion():
    """Test 5.8: TODO.md tracks phase completion"""
    with open('TODO.md', 'r') as f:
        todo = f.read()
    
    # Check all phases are documented
    phases = ['Phase 0', 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'Phase 5']
    for phase in phases:
        assert phase in todo, f"TODO.md missing: {phase}"
    
    # Check completed phases are marked
    completed_phases = ['Phase 0', 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4']
    for phase in completed_phases:
        # Look for completion markers like ✅ or "COMPLETE"
        assert '✅' in todo or 'COMPLETE' in todo, f"Completed phases should be marked"
    
    print("✓ Test 5.8 PASSED: TODO.md properly tracks all phases")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
