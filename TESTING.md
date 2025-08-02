# Testing Documentation

This project includes a comprehensive test suite covering all major components and functionality.

## 🧪 Test Structure

```
tests/
├── conftest.py          # Test configuration and fixtures
├── test_api.py          # API endpoint tests  
├── test_admin.py        # Admin functionality tests
├── test_models.py       # Database model tests
└── test_integration.py  # Integration and performance tests
```

## 🚀 Running Tests

### Prerequisites
```bash
cd backend
pip install -r requirements.txt
```

### Basic Test Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_api.py -v

# Run specific test
python -m pytest tests/test_api.py::TestHealthEndpoint::test_health_check -v
```

### Test Categories

```bash
# Unit tests only
python -m pytest tests/ -m unit

# Integration tests only
python -m pytest tests/ -m integration

# Skip slow tests
python -m pytest tests/ -m "not slow"
```

## 📊 Coverage Reports

Test coverage reports are generated in multiple formats:

- **Terminal**: Shows coverage summary with missing lines
- **HTML**: Detailed coverage report in `htmlcov/index.html`
- **XML**: Machine-readable coverage for CI/CD in `coverage.xml`

```bash
# Generate all coverage reports
python -m pytest tests/ --cov=app --cov-report=html --cov-report=xml --cov-report=term
```

## 🔧 Test Configuration

Tests are configured via `pytest.ini`:

- **Test Discovery**: Automatically finds test files matching `test_*.py`
- **Async Support**: Enables `asyncio_mode = auto` for async test functions
- **Coverage**: Configured to measure backend app coverage
- **Markers**: Custom markers for test categorization

## 🗄️ Database Testing

Tests use **mongomock** for in-memory MongoDB simulation:

- No external database required for testing
- Isolated test environment
- Fast test execution
- Automatic cleanup between tests

## 🔒 Security & Quality

The test suite includes:

- **Input validation** testing
- **Error handling** verification
- **File upload limits** validation
- **API endpoint security** checks
- **Performance** testing with large datasets

## 📋 Test Fixtures

Available fixtures in `conftest.py`:

- `mock_db`: In-memory MongoDB instance
- `client`: FastAPI test client
- `sample_provider`: Pre-created test provider
- `sample_analysis`: Pre-created test analysis

## 🐛 Debugging Tests

```bash
# Run with verbose output
python -m pytest tests/ -v -s

# Stop on first failure
python -m pytest tests/ -x

# Drop into debugger on failure
python -m pytest tests/ --pdb

# Run only failed tests from last run
python -m pytest tests/ --lf
```

## 📈 Continuous Integration

Tests run automatically on:

- **Push** to main/develop branches
- **Pull requests** to main/develop
- **Multiple Python versions** (3.9, 3.10, 3.11)

The CI pipeline includes:

1. **Unit & Integration Tests**
2. **Code Coverage** reporting  
3. **Code Quality** checks (Black, isort, flake8, mypy)
4. **Security Scanning** (Bandit, Safety)
5. **Docker Build** testing

## 📝 Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test Structure

```python
import pytest
from httpx import AsyncClient

class TestNewFeature:
    """Test new feature functionality"""
    
    @pytest.mark.asyncio
    async def test_feature_success(self, client: AsyncClient):
        """Test successful feature operation"""
        response = await client.get("/api/v1/new-feature")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_feature_error_handling(self, client: AsyncClient):
        """Test feature error handling"""
        response = await client.get("/api/v1/new-feature?invalid=param")
        assert response.status_code == 400
```

### Async Test Guidelines
- Use `@pytest.mark.asyncio` for async test functions
- Use `async with` for context managers
- Properly await all async operations

### Database Test Guidelines
- Use provided fixtures for database setup
- Each test gets a clean database state
- No manual cleanup required

## 🎯 Test Coverage Goals

Target coverage levels:
- **Overall**: > 90%
- **API endpoints**: 100%
- **Database models**: > 95%
- **Core business logic**: 100%
- **Error handling**: > 90%

Current coverage can be viewed by running:
```bash
python -m pytest tests/ --cov=app --cov-report=term-missing
```