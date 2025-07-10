# GitHub Actions Workflows - EspoCRM Client

## 📋 Genel Bakış

Bu dokümantasyon, EspoCRM Python Client projesi için gerekli GitHub Actions workflow'larını detaylandırır.

## 🔄 Workflow Yapısı

### 1. Continuous Integration (CI) - `ci.yml`

**Tetikleyiciler:**
- Push to main branch
- Pull requests to main
- Manual dispatch

**İşler:**
- **test**: Multi-platform, multi-Python version testing
- **quality**: Code quality checks
- **security**: Security scanning
- **docs**: Documentation build test

**Matrix Strategy:**
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
```

### 2. Release Automation - `release.yml`

**Tetikleyiciler:**
- Git tag push (v*.*.*)

**İşler:**
- **build**: Package building
- **test-pypi**: Test PyPI upload
- **validate**: Installation validation
- **pypi**: Production PyPI upload
- **github-release**: GitHub release creation

### 3. Documentation - `docs.yml`

**Tetikleyiciler:**
- Push to main (docs/ changes)
- Manual dispatch

**İşler:**
- **build-docs**: MkDocs build
- **deploy**: GitHub Pages deployment

## 📁 Workflow Dosyaları

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest --cov=espocrm --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'

  quality:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Code formatting check
      run: |
        black --check espocrm tests
        isort --check-only espocrm tests
    
    - name: Type checking
      run: mypy espocrm
    
    - name: Linting
      run: flake8 espocrm tests
    
    - name: Package validation
      run: python scripts/validate_package.py

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install bandit safety
    
    - name: Security scan
      run: |
        bandit -r espocrm
        safety check
```

### `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Check package
      run: twine check dist/*
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: dist
        path: dist/

  test-pypi:
    needs: build
    runs-on: ubuntu-latest
    environment: test-pypi
    steps:
    - name: Download artifacts
      uses: actions/download-artifact@v3
      with:
        name: dist
        path: dist/
    
    - name: Publish to Test PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        repository-url: https://test.pypi.org/legacy/
        password: ${{ secrets.TEST_PYPI_API_TOKEN }}

  validate:
    needs: test-pypi
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Test installation from Test PyPI
      run: |
        sleep 60  # Wait for package to be available
        pip install --index-url https://test.pypi.org/simple/ \
                   --extra-index-url https://pypi.org/simple/ \
                   espocrm-client
        python -c "import espocrm; print(f'Successfully imported v{espocrm.__version__}')"

  pypi:
    needs: validate
    runs-on: ubuntu-latest
    environment: pypi
    steps:
    - name: Download artifacts
      uses: actions/download-artifact@v3
      with:
        name: dist
        path: dist/
    
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}

  github-release:
    needs: pypi
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        files: dist/*
        generate_release_notes: true
        draft: false
        prerelease: false
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### `.github/workflows/docs.yml`

```yaml
name: Documentation

on:
  push:
    branches: [ main ]
    paths: [ 'docs/**', 'mkdocs.yml' ]
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[docs]"
    
    - name: Build documentation
      run: mkdocs build
    
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./site
```

## 🔐 GitHub Secrets Yapılandırması

### Gerekli Secrets

1. **PYPI_API_TOKEN**
   - PyPI hesabından oluşturulan API token
   - Scope: Bu proje için sınırlı

2. **TEST_PYPI_API_TOKEN**
   - Test PyPI hesabından oluşturulan API token
   - Test yüklemeleri için

3. **CODECOV_TOKEN** (opsiyonel)
   - Code coverage raporlama için

### Environment Yapılandırması

GitHub repository settings'de environments oluştur:

1. **test-pypi**
   - Protection rules: None
   - Secrets: TEST_PYPI_API_TOKEN

2. **pypi**
   - Protection rules: Required reviewers (repository admins)
   - Secrets: PYPI_API_TOKEN

## 📊 Status Badges

README.md'ye eklenecek badges:

```markdown
[![CI](https://github.com/username/espocrm-client/workflows/CI/badge.svg)](https://github.com/username/espocrm-client/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/espocrm-client.svg)](https://badge.fury.io/py/espocrm-client)
[![Python versions](https://img.shields.io/pypi/pyversions/espocrm-client.svg)](https://pypi.org/project/espocrm-client/)
[![Coverage](https://codecov.io/gh/username/espocrm-client/branch/main/graph/badge.svg)](https://codecov.io/gh/username/espocrm-client)
```

## 🔄 Workflow Optimizasyonları

### Caching
- pip cache
- pytest cache
- mypy cache

### Parallelization
- Matrix builds
- Concurrent jobs
- Artifact sharing

### Performance
- Minimal dependencies
- Efficient test selection
- Smart triggering

## 📋 Kurulum Adımları

1. **Workflow dosyalarını oluştur**
   ```bash
   mkdir -p .github/workflows
   # Workflow dosyalarını kopyala
   ```

2. **GitHub Secrets'ı yapılandır**
   - Repository Settings > Secrets and variables > Actions
   - Gerekli secrets'ları ekle

3. **Environments'ı oluştur**
   - Repository Settings > Environments
   - test-pypi ve pypi environments'ı oluştur

4. **Branch protection'ı aktifleştir**
   - Repository Settings > Branches
   - main branch için protection rules ekle

## ✅ Test Checklist

### CI Workflow
- [ ] Tüm Python versiyonlarında testler geçiyor
- [ ] Tüm platformlarda testler geçiyor
- [ ] Code quality checks geçiyor
- [ ] Security scans temiz

### Release Workflow
- [ ] Package build başarılı
- [ ] Test PyPI upload başarılı
- [ ] Test PyPI'den kurulum başarılı
- [ ] Production PyPI upload başarılı
- [ ] GitHub release oluşturuluyor

### Documentation Workflow
- [ ] Documentation build başarılı
- [ ] GitHub Pages deployment başarılı

---

**Not**: Bu workflow'lar, projenin profesyonel standartlarda CI/CD süreçlerine sahip olmasını sağlar.