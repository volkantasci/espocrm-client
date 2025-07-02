# Release Checklist

This checklist ensures that all necessary steps are completed before releasing a new version of EspoCRM Python Client.

## Pre-Release Preparation

### 1. Code Quality
- [ ] All tests pass locally (`pytest`)
- [ ] Code coverage is above 90% (`pytest --cov=espocrm --cov-fail-under=90`)
- [ ] Code formatting is correct (`black --check espocrm tests`)
- [ ] Imports are sorted (`isort --check-only espocrm tests`)
- [ ] Type checking passes (`mypy espocrm`)
- [ ] Linting passes (`flake8 espocrm tests`)
- [ ] Security scan passes (`bandit -r espocrm`)
- [ ] No TODO or FIXME comments in production code

### 2. Documentation
- [ ] README.md is up to date
- [ ] CHANGELOG.md has entry for new version
- [ ] All documentation builds without errors (`mkdocs build --strict`)
- [ ] API documentation is complete
- [ ] Examples are working and up to date
- [ ] Installation instructions are correct

### 3. Version Management
- [ ] Version number follows semantic versioning
- [ ] Version is updated in `espocrm/__init__.py`
- [ ] Version is updated in `pyproject.toml`
- [ ] Version matches between all files
- [ ] Git tag is ready to be created

### 4. Package Validation
- [ ] Package structure is correct
- [ ] All required files are included
- [ ] MANIFEST.in is up to date
- [ ] Package builds successfully (`python -m build`)
- [ ] Built package passes validation (`twine check dist/*`)
- [ ] Package installs correctly in clean environment
- [ ] CLI tool works after installation

## Release Process

### 1. Final Testing
- [ ] Run full test suite on all supported Python versions
- [ ] Test installation from built wheel
- [ ] Test CLI functionality
- [ ] Test import of all public APIs
- [ ] Verify examples work with new version

### 2. Version Bump
```bash
# Use version manager script
python scripts/version_manager.py bump [major|minor|patch] --update-changelog
```

- [ ] Version bumped correctly
- [ ] CHANGELOG.md updated
- [ ] All version references updated

### 3. Git Operations
```bash
# Commit version changes
git add .
git commit -m "Bump version to X.Y.Z"

# Create and push tag
git tag -a vX.Y.Z -m "Release version X.Y.Z"
git push origin main
git push origin vX.Y.Z
```

- [ ] Changes committed
- [ ] Tag created and pushed
- [ ] GitHub release created

### 4. Package Build and Upload
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build package
python -m build

# Check package
twine check dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ espocrm-python-client

# Upload to PyPI
twine upload dist/*
```

- [ ] Package built successfully
- [ ] Package uploaded to TestPyPI
- [ ] Installation from TestPyPI tested
- [ ] Package uploaded to PyPI
- [ ] Installation from PyPI verified

### 5. Post-Release
- [ ] GitHub release notes published
- [ ] Documentation deployed
- [ ] Social media announcement (if applicable)
- [ ] Update project status badges
- [ ] Notify users/community

## Automated Checks (CI/CD)

The following should be automated via GitHub Actions:

### On Pull Request
- [ ] Tests run on all supported Python versions
- [ ] Code quality checks pass
- [ ] Documentation builds successfully
- [ ] Package validation passes

### On Release
- [ ] Full test suite runs
- [ ] Package builds and validates
- [ ] Automatic upload to PyPI
- [ ] Documentation deployment
- [ ] GitHub release creation

## Rollback Plan

If issues are discovered after release:

### Minor Issues
- [ ] Create hotfix branch
- [ ] Fix issue
- [ ] Release patch version
- [ ] Update documentation

### Major Issues
- [ ] Yank problematic version from PyPI
- [ ] Create GitHub issue explaining the problem
- [ ] Work on fix
- [ ] Release corrected version
- [ ] Communicate with users

## Version-Specific Checklists

### Major Version (X.0.0)
- [ ] Breaking changes documented
- [ ] Migration guide created
- [ ] Deprecation warnings added in previous version
- [ ] Backward compatibility considerations
- [ ] Extended testing period

### Minor Version (X.Y.0)
- [ ] New features documented
- [ ] Examples updated for new features
- [ ] Backward compatibility maintained
- [ ] Feature flags considered for experimental features

### Patch Version (X.Y.Z)
- [ ] Bug fixes documented
- [ ] No new features added
- [ ] Regression tests added
- [ ] Security fixes prioritized

### Pre-release (X.Y.Z-alpha/beta/rc)
- [ ] Clearly marked as pre-release
- [ ] Limited distribution
- [ ] Feedback collection plan
- [ ] Timeline for stable release

## Tools and Scripts

### Useful Commands
```bash
# Check current version
python scripts/version_manager.py current

# Validate package
python scripts/validate_package.py

# Build documentation
mkdocs build

# Run all tests
pytest --cov=espocrm

# Security scan
bandit -r espocrm

# Check package
twine check dist/*
```

### Environment Setup
```bash
# Install development dependencies
pip install -e ".[dev]"

# Install build tools
pip install build twine

# Install documentation tools
pip install -e ".[docs]"
```

## Contact Information

- **Release Manager**: [Name] <email@example.com>
- **Technical Lead**: [Name] <email@example.com>
- **Documentation**: [Name] <email@example.com>

## Emergency Contacts

- **PyPI Account**: [Account details]
- **GitHub Admin**: [Account details]
- **Documentation Host**: [Account details]

---

**Note**: This checklist should be updated as the project evolves. Always review and update the checklist before each release.