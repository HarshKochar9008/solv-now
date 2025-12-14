# Testing Guide

This document provides information about testing the LinkedIn Insights Microservice.

## Quick Test

Run the simple test script:
```bash
python test_app.py
```

This will test:
- Configuration loading
- Root endpoint
- Health check endpoint
- Search pages endpoint

## Test Structure

### Test Files

- `test_app.py`: Simple test script that doesn't require pytest (recommended for quick testing)
- `tests/test_main.py`: Comprehensive pytest tests for all API endpoints
- `tests/test_config.py`: Configuration tests
- `tests/conftest.py`: Pytest fixtures and test setup

### Running Tests

#### Option 1: Simple Test Script (Recommended)
```bash
python test_app.py
```

#### Option 2: Pytest (if available)
```bash
pytest tests/ -v
```

#### Option 3: With Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

## Test Coverage

The test suite covers:

1. **Configuration Tests**
   - Settings loading
   - Environment variable parsing
   - Default values

2. **API Endpoint Tests**
   - Root endpoint (`/`)
   - Health check (`/health`)
   - Search pages (`/api/pages`)
   - Get page by ID (`/api/pages/{page_id}`)
   - Get page employees (`/api/pages/{page_id}/employees`)
   - Get page posts (`/api/pages/{page_id}/posts`)
   - Pagination
   - Filtering

3. **Database Tests**
   - In-memory SQLite database for testing
   - Fresh database for each test
   - Data persistence and retrieval

## Test Environment

Tests use an in-memory SQLite database to ensure:
- Fast test execution
- No side effects on development database
- Isolated test runs

## Manual Testing

You can also test the API manually:

1. Start the server:
   ```bash
   python run.py
   ```

2. Test endpoints:
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Root endpoint
   curl http://localhost:8000/
   
   # Search pages
   curl http://localhost:8000/api/pages
   ```

3. View API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Pytest Issues

If you encounter issues with pytest (e.g., langsmith plugin conflicts), use the simple test script instead:
```bash
python test_app.py
```

### Environment Variables

Make sure your `.env` file exists and has valid values. The test script will use default values if the file is missing.

### Database Issues

Tests use an in-memory database, so no database file is needed for testing. If you encounter database-related errors, check that SQLAlchemy is properly installed.





