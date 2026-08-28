# Deep Eye - Contributing Guide

Thank you for your interest in contributing to Deep Eye! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and professional
- Follow ethical security practices
- Never use this tool for illegal purposes
- Report security issues responsibly

## How to Contribute

### 1. Fork the Repository
```bash
git clone https://github.com/zakirkun/deep-eye.git
cd deep-eye
```

### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes
- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Update tests if applicable
- Update documentation

### 4. Test Your Changes
```bash
python -m pytest tests/
```

### 5. Submit Pull Request
- Write clear commit messages
- Reference any related issues
- Update CHANGELOG.md

## Development Setup

### Install Development Dependencies
```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Tests
```powershell
pytest tests/ -v
```

### Code Formatting
```powershell
# Lint / format (ruff preferred; black/flake8 optional if installed)
ruff check .
ruff format .
```

## Project Structure

```
deep-eye/
├── core/               # Core scanning engine
├── ai_providers/       # AI provider integrations
├── modules/           # Security testing modules
├── utils/             # Utility functions
├── config/            # Configuration files
├── templates/         # Nuclei-style YAML templates (+ report assets)
├── tests/             # Unit tests
└── examples/          # Usage examples
```

## Adding New Features

### Adding a New Vulnerability Check
1. Create package under `modules/<name>/` with `__init__.py` and tester class
2. Constructor `(http_client, config)`, method `scan(url, context=None) -> List[Dict]`
3. Wire in `core/vulnerability_scanner.py` or `ScannerEngine._init_extra_module_testers`
4. Add name to `config/config.example.yaml` `vulnerability_scanner.enabled_checks`
5. Update documentation

### Adding a New AI Provider
1. Create provider class in `ai_providers/`
2. Implement `generate(prompt, **kwargs) -> str`
3. Register in `provider_manager._initialize_providers`
4. Update configuration template

### Adding Report Formats
1. Create builder in `utils/exports/`
2. Export from `utils/exports/__init__.py`
3. Wire format in `report_generator.py` / CLI `--formats`
4. Update documentation

## Security

### Reporting Security Issues
- **DO NOT** open public issues for security vulnerabilities
- Email: security@deepeye.io
- Use PGP key if available
- Provide detailed reproduction steps

### Security Best Practices
- Never commit API keys or secrets
- Use environment variables for sensitive data
- Follow OWASP guidelines
- Implement rate limiting
- Add input validation

## Documentation

- Keep README.md up to date
- Add docstrings to all public APIs
- Update QUICKSTART.md for new features
- Include code examples

## Testing Guidelines

- Write unit tests for new features
- Prefer tests for new Hanzou-era modules; expand core coverage when touching core
- Test edge cases
- Mock external API calls

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Open an issue with the "question" label or contact the maintainers.

---

**Thank you for contributing to Deep Eye! 🔍🛡️**
