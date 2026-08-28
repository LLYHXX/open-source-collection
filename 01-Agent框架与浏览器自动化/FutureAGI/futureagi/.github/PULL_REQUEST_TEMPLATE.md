## Description

<!-- Provide a brief description of your changes -->

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Configuration change

## Checklist

### Code Quality

- [ ] I have run `make pre-commit-all` and fixed all issues
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas

### Testing

- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have run `make test` successfully

### Django-Specific (if applicable)

- [ ] I have created/updated migrations if model changes were made
- [ ] I have run `python manage.py check` without errors
- [ ] Database migrations are reversible

### Documentation

- [ ] I have updated the documentation accordingly
- [ ] I have added/updated docstrings for new/modified functions
- [ ] I have updated the CHANGELOG (if applicable)

### Security

- [ ] My changes don't introduce security vulnerabilities
- [ ] I have not committed any secrets or credentials
- [ ] I have run `make check-secrets` and addressed any issues

## Pre-commit Hooks

- [ ] ✅ Pre-commit hooks are installed (`make pre-commit-install`)
- [ ] ✅ All pre-commit checks pass (`make pre-commit-all`)

**If you haven't set up pre-commit yet:**
```bash
make pre-commit-install
make pre-commit-all
```

See [Pre-commit Setup Guide](../blob/main/docs/PRE_COMMIT_SETUP.md) for details.

## Related Issues

<!-- Link to related issues: Fixes #123, Related to #456 -->

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->

## Additional Notes

<!-- Add any additional notes or context about the PR -->

---

**Reviewer Guidelines:**
- Ensure all checkboxes are checked
- Verify pre-commit checks have passed in CI
- Check code quality and test coverage
