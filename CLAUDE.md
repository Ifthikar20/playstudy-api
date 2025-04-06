# CLAUDE.md - Guidelines for AI Coding Assistants

## Commands
- Format: `black .` & `isort .`
- Lint: `flake8`
- Type check: `mypy`
- Run all tests: `pytest`
- Run test subsets: `pytest tests/unit` or `pytest tests/integration`
- Run single test: `pytest tests/path/to/test_file.py::test_function_name -v`
- Coverage: `pytest --cov=app tests/`

## Code Style Guidelines
- **Types**: Use strong typing with mypy. Mark nullable fields with `Optional`.
- **Imports**: Standard library → third-party → local imports (sorted with isort)
- **Formatting**: Black with default settings
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error handling**: Use custom exceptions from `app.core.exceptions`, ensure proper logging
- **Architecture**: Follow clean architecture with domain models, repositories, services
- **API patterns**: Use FastAPI dependency injection, consistent response schemas
- **Documentation**: Docstrings for all public functions and classes