# RAG Testing Guide

This document provides comprehensive information about the testing suite for the RAG project.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Test Configuration](#test-configuration)
6. [Writing Tests](#writing-tests)
7. [Test Database](#test-database)
8. [Coverage Reports](#coverage-reports)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## 🎯 Overview

The RAG testing suite provides comprehensive coverage for all components of the system:

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test the interaction between different components
- **API Tests**: Test the FastAPI endpoints and responses
- **Database Tests**: Test database models and operations
- **Authentication Tests**: Test user registration, login, and authorization
- **File Processing Tests**: Test file upload, processing, and retrieval
- **LLM Integration Tests**: Test LLM provider interactions
- **Vector Database Tests**: Test vector database operations

## 📁 Test Structure

```
src/helpers/tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration & fixtures
├── requirements-test.txt       # Test dependencies
├── models/                     # Database model tests
│   ├── __init__.py
│   ├── test_project_model.py   # Project CRUD operations
│   ├── test_asset_model.py     # File asset management
│   └── test_chunk_model.py     # Text chunking operations
├── controllers/                # Business logic tests
│   ├── __init__.py
│   └── test_nlp_controller.py  # NLP operations
├── routes/                     # API endpoint tests
│   ├── __init__.py
│   ├── test_auth_routes.py     # Authentication endpoints
│   └── test_data_routes.py     # Data management endpoints
├── stores/                     # External service tests
│   ├── __init__.py
│   └── test_llm_providers.py   # LLM provider testing
├── utils/                      # Utility function tests
│   ├── __init__.py
│   └── test_error_handler.py   # Error handling utilities
└── integration/                # End-to-end tests
    ├── __init__.py
    └── test_full_workflow.py   # Complete user workflows
```

## 🚀 Running Tests

### Quick Start

```bash
# Run all tests
./run_tests.sh

# Run specific test categories
./run_tests.sh unit
./run_tests.sh integration
./run_tests.sh models
./run_tests.sh routes
./run_tests.sh controllers
./run_tests.sh stores
./run_tests.sh utils

# Run with coverage
./run_tests.sh coverage

# Get help
./run_tests.sh help
```

### Manual Execution

```bash
# Install test dependencies
pip install -r src/helpers/tests/requirements-test.txt

# Run all tests
pytest src/helpers/tests/ -v

# Run specific test file
pytest src/helpers/tests/models/test_project_model.py -v

# Run tests with markers
pytest src/helpers/tests/ -m "unit" -v
pytest src/helpers/tests/ -m "integration" -v

# Run with coverage
pytest src/helpers/tests/ --cov=src --cov-report=html --cov-report=term-missing
```

## 🏷️ Test Categories

### Unit Tests (`@pytest.mark.unit`)

Test individual components in isolation:

- **Models**: Database model operations, CRUD operations
- **Controllers**: Business logic, data processing
- **Utils**: Utility functions, error handling
- **Stores**: LLM providers, vector database providers

### Integration Tests (`@pytest.mark.integration`)

Test component interactions:

- **Full Workflow**: Complete user journey from registration to query
- **Multi-user Isolation**: User data separation
- **File Processing**: Upload, process, retrieve workflow
- **Error Handling**: End-to-end error scenarios

### Route Tests (`@pytest.mark.routes`)

Test API endpoints:

- **Authentication**: Registration, login, token validation
- **Data Operations**: Project CRUD, file upload, processing
- **NLP Operations**: Indexing, searching, answering
- **Error Responses**: Invalid requests, missing data

### Model Tests (`@pytest.mark.models`)

Test database operations:

- **Project Model**: Project creation, retrieval, deletion
- **Asset Model**: File asset management
- **Chunk Model**: Text chunking and storage
- **User Model**: User management

### Controller Tests (`@pytest.mark.controllers`)

Test business logic:

- **NLP Controller**: Vector operations, LLM interactions
- **Process Controller**: File processing, chunking
- **Data Controller**: Data management operations

### Store Tests (`@pytest.mark.stores`)

Test external service integrations:

- **LLM Providers**: OpenAI, Cohere integrations
- **Vector Database**: Qdrant, PGVector operations
- **Provider Factory**: Provider creation and configuration

### Utils Tests (`@pytest.mark.utils`)

Test utility functions:

- **Error Handler**: Exception handling, response formatting
- **Authentication**: Token validation, user verification
- **File Processing**: Text extraction, format handling

## ⚙️ Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = src/helpers/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    auth: Authentication related tests
    models: Database model tests
    routes: API route tests
    controllers: Controller tests
    stores: Store provider tests
    utils: Utility function tests
asyncio_mode = auto
```

### Test Fixtures (`conftest.py`)

Common fixtures available to all tests:

- `test_client`: FastAPI test client
- `test_session`: Database session for testing
- `mock_user`: Mock user object
- `mock_project`: Mock project object
- `mock_asset`: Mock asset object
- `mock_chunk`: Mock chunk object
- `mock_llm_client`: Mock LLM client
- `mock_vector_db_client`: Mock vector database client
- `mock_settings`: Mock configuration settings

## ✍️ Writing Tests

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, Mock, patch

class TestYourClass:
    """Test cases for YourClass."""
    
    @pytest.mark.asyncio
    async def test_method_success(self, test_session):
        """Test successful method execution."""
        # Arrange
        # Set up test data and mocks
        
        # Act
        # Call the method being tested
        
        # Assert
        # Verify the expected behavior
        assert result is not None
        assert result.property == expected_value
```

### Test Markers

Use appropriate markers for test categorization:

```python
@pytest.mark.unit
@pytest.mark.models
async def test_project_creation(self, test_session):
    """Test project creation."""
    pass

@pytest.mark.integration
@pytest.mark.slow
async def test_full_workflow(self, test_client):
    """Test complete user workflow."""
    pass
```

### Mocking Best Practices

```python
# Mock external dependencies
with patch('module.ExternalService') as mock_service:
    mock_service.return_value.method.return_value = expected_result
    
    result = await your_function()
    assert result == expected_result

# Mock database operations
test_session.execute = AsyncMock()
test_session.execute.return_value.scalar_one_or_none.return_value = mock_object

# Mock API responses
with patch('routes.auth.get_current_active_user') as mock_get_user:
    mock_user = Mock()
    mock_user.user_id = 1
    mock_get_user.return_value = mock_user
```

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_function(self):
    """Test async function."""
    result = await your_async_function()
    assert result is not None
```

## 🗄️ Test Database

### Setup

The test suite uses a separate test database (`minirag_test`) to avoid affecting production data.

```bash
# Create test database
createdb -h localhost -U postgres minirag_test

# Run migrations on test database
cd src/models/db_schemes/minirag
alembic upgrade head
```

### Configuration

Test database configuration in `conftest.py`:

```python
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/minirag_test"
```

### Cleanup

Tests automatically clean up after themselves using pytest fixtures and database transactions.

## 📊 Coverage Reports

### HTML Coverage Report

```bash
# Generate HTML coverage report
pytest src/helpers/tests/ --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

### Terminal Coverage Report

```bash
# Show coverage in terminal
pytest src/helpers/tests/ --cov=src --cov-report=term-missing
```

### Coverage Configuration

Coverage settings in `pytest.ini`:

```ini
addopts = 
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
```

## 📋 Best Practices

### Test Organization

1. **Group related tests** in the same test class
2. **Use descriptive test names** that explain the scenario
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Keep tests independent** - no test should depend on another
5. **Use appropriate markers** for test categorization

### Test Data

1. **Use fixtures** for common test data
2. **Create realistic test data** that represents real usage
3. **Clean up test data** after tests complete
4. **Use factories** for complex object creation

### Mocking

1. **Mock external dependencies** (APIs, databases, file systems)
2. **Mock at the right level** - mock interfaces, not implementations
3. **Verify mock calls** when testing interactions
4. **Use AsyncMock** for async functions

### Error Testing

1. **Test error conditions** and edge cases
2. **Verify error messages** are user-friendly
3. **Test exception handling** and recovery
4. **Test invalid input** and boundary conditions

### Performance

1. **Use appropriate markers** for slow tests (`@pytest.mark.slow`)
2. **Run fast tests frequently** during development
3. **Run slow tests** before deployment
4. **Use parallel execution** for independent tests

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -h localhost -U postgres -l | grep minirag_test

# Create test database if missing
createdb -h localhost -U postgres minirag_test
```

#### Import Errors

```bash
# Ensure virtual environment is activated
source src/venv/bin/activate

# Install test dependencies
pip install -r src/helpers/tests/requirements-test.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Test Failures

1. **Check test database** is properly set up
2. **Verify mocks** are correctly configured
3. **Check async/await** usage in async tests
4. **Review test data** for correctness

### Debugging Tests

```bash
# Run single test with verbose output
pytest src/helpers/tests/models/test_project_model.py::TestProjectModel::test_create_instance -v -s

# Run with debugger
pytest src/helpers/tests/ --pdb

# Run with print statements
pytest src/helpers/tests/ -s
```

### Test Reports

```bash
# Generate HTML report
pytest src/helpers/tests/ --html=test_report.html --self-contained-html

# Generate JUnit XML report
pytest src/helpers/tests/ --junitxml=test_results.xml
```

## 📈 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r src/requirements.txt
          pip install -r src/helpers/tests/requirements-test.txt
      - name: Run tests
        run: |
          ./run_tests.sh coverage
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Pytest-cov](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

For questions or issues with the testing suite, please refer to the project documentation or create an issue in the repository. 