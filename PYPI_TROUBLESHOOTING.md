# PyPI Troubleshooting Guide - EspoCRM Client

## 🚨 Yaygın Sorunlar ve Çözümleri

Bu rehber, PyPI yükleme sürecinde karşılaşılabilecek sorunları ve çözümlerini detaylandırır.

## 🔧 Build ve Package Sorunları

### 1. Package Build Hatası

**Hata:**
```bash
ERROR: Failed building wheel for espocrm-client
```

**Çözümler:**
```bash
# 1. Dependencies kontrol et
pip install --upgrade setuptools wheel build

# 2. Python version uyumluluğu
python --version  # 3.8+ olmalı

# 3. pyproject.toml syntax kontrol
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"

# 4. Temiz build
rm -rf build/ dist/ *.egg-info/
python -m build
```

### 2. Import Path Sorunları

**Hata:**
```bash
ModuleNotFoundError: No module named 'espocrm'
```

**Çözümler:**
```bash
# 1. Package structure kontrol
ls -la espocrm/
# __init__.py dosyası olmalı

# 2. PYTHONPATH kontrol
python -c "import sys; print(sys.path)"

# 3. Editable install test
pip install -e .
python -c "import espocrm; print(espocrm.__version__)"
```

### 3. Version Conflict

**Hata:**
```bash
ERROR: Version '0.1.0' already exists
```

**Çözümler:**
```bash
# 1. Version bump
python scripts/version_manager.py bump patch

# 2. Manual version update
# pyproject.toml ve __init__.py'de version güncelle

# 3. Git tag kontrol
git tag -l
git tag -d v0.1.0  # Gerekirse local tag sil
```

## 🔐 Authentication Sorunları

### 1. API Token Hatası

**Hata:**
```bash
HTTP Error 403: Invalid or non-existent authentication information
```

**Çözümler:**
```bash
# 1. Token format kontrol
# Token "pypi-" ile başlamalı

# 2. Username __token__ olmalı
python -m twine upload --username __token__ --password pypi-xxx dist/*

# 3. Token scope kontrol
# PyPI'de token settings'i kontrol et

# 4. .pypirc dosyası oluştur
cat > ~/.pypirc << EOF
[distutils]
index-servers = pypi testpypi

[pypi]
username = __token__
password = pypi-your-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-token-here
EOF
```

### 2. 2FA Sorunları

**Hata:**
```bash
Two-factor authentication required
```

**Çözümler:**
```bash
# 1. API token kullan (2FA bypass)
# Username/password yerine token kullan

# 2. 2FA app kontrol
# Google Authenticator, Authy vb.

# 3. Recovery codes kullan
# PyPI hesap settings'den
```

## 📦 Upload Sorunları

### 1. Package Name Conflict

**Hata:**
```bash
HTTP Error 403: The user 'username' isn't allowed to upload to project 'espocrm-client'
```

**Çözümler:**
```bash
# 1. Paket adı müsaitlik kontrol
# https://pypi.org/project/espocrm-client/

# 2. Farklı isim seç
# pyproject.toml'de name değiştir

# 3. Mevcut maintainer'dan izin al
# PyPI'de proje sayfasından iletişim
```

### 2. File Size Limit

**Hata:**
```bash
HTTP Error 413: Request Entity Too Large
```

**Çözümler:**
```bash
# 1. Package size kontrol
du -sh dist/*

# 2. Gereksiz dosyaları exclude et
# MANIFEST.in'de global-exclude ekle

# 3. .gitignore kontrol
# Build artifacts dahil edilmemeli
```

### 3. Network Timeout

**Hata:**
```bash
ReadTimeoutError: HTTPSConnectionPool
```

**Çözümler:**
```bash
# 1. Retry ile upload
python -m twine upload --verbose --skip-existing dist/*

# 2. Timeout artır
python -m twine upload --timeout 300 dist/*

# 3. Network bağlantısı kontrol
ping pypi.org
```

## 🧪 Test Sorunları

### 1. Test PyPI Import Hatası

**Hata:**
```bash
No module named 'requests'
```

**Çözümler:**
```bash
# 1. Extra index URL kullan
pip install --index-url https://test.pypi.org/simple/ \
           --extra-index-url https://pypi.org/simple/ \
           espocrm-client

# 2. Dependencies manual install
pip install requests pydantic structlog
pip install --index-url https://test.pypi.org/simple/ espocrm-client

# 3. Requirements check
pip show espocrm-client
```

### 2. CLI Command Not Found

**Hata:**
```bash
espocrm-cli: command not found
```

**Çözümler:**
```bash
# 1. Entry points kontrol
pip show -f espocrm-client | grep scripts

# 2. PATH kontrol
echo $PATH
which espocrm-cli

# 3. Manual execution
python -m espocrm.cli --version

# 4. Reinstall
pip uninstall espocrm-client
pip install espocrm-client
```

## 🔄 GitHub Actions Sorunları

### 1. Workflow Permission Denied

**Hata:**
```bash
Error: Resource not accessible by integration
```

**Çözümler:**
```bash
# 1. Repository permissions kontrol
# Settings > Actions > General > Workflow permissions

# 2. GITHUB_TOKEN permissions
# workflow dosyasında permissions ekle:
permissions:
  contents: write
  packages: write

# 3. Personal Access Token kullan
# Fine-grained token oluştur
```

### 2. Secret Not Found

**Hata:**
```bash
Error: Secret PYPI_API_TOKEN not found
```

**Çözümler:**
```bash
# 1. Secret name kontrol
# Repository Settings > Secrets and variables > Actions

# 2. Environment secrets
# Environment-specific secrets kontrol et

# 3. Organization secrets
# Organization level secrets kontrol et
```

### 3. Matrix Build Failures

**Hata:**
```bash
Some matrix jobs failed
```

**Çözümler:**
```bash
# 1. fail-fast: false ekle
strategy:
  fail-fast: false
  matrix:
    python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

# 2. Platform-specific fixes
# Windows için özel komutlar

# 3. Dependency conflicts
# Version pinning yap
```

## 🐛 Runtime Sorunları

### 1. Import Circular Dependency

**Hata:**
```bash
ImportError: cannot import name 'X' from partially initialized module
```

**Çözümler:**
```bash
# 1. Import order kontrol
# __init__.py'de import sırası

# 2. Lazy import kullan
def get_client():
    from .client import EspoCRMClient
    return EspoCRMClient

# 3. Import structure refactor
# Circular dependency'yi kır
```

### 2. Version Mismatch

**Hata:**
```bash
AttributeError: module 'espocrm' has no attribute 'new_feature'
```

**Çözümler:**
```bash
# 1. Version kontrol
python -c "import espocrm; print(espocrm.__version__)"

# 2. Cache temizle
pip cache purge
pip uninstall espocrm-client
pip install espocrm-client

# 3. Virtual environment yenile
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install espocrm-client
```

## 📊 Monitoring ve Debug

### 1. Package Statistics

```bash
# Download stats
curl -s https://pypistats.org/api/packages/espocrm-client/recent

# Package info
curl -s https://pypi.org/pypi/espocrm-client/json | jq .info.version
```

### 2. Debug Installation

```bash
# Verbose install
pip install -v espocrm-client

# Show package files
pip show -f espocrm-client

# Check dependencies
pip check espocrm-client
```

### 3. Test Environment

```bash
# Clean test environment
docker run --rm -it python:3.11-slim bash
pip install espocrm-client
python -c "import espocrm; print('OK')"
```

## 🔧 Emergency Procedures

### 1. Package Yanking

```bash
# PyPI'de package yank et (emergency)
# PyPI web interface kullan
# "Yank release" option

# Reason belirt
# "Critical security vulnerability"
```

### 2. Hotfix Release

```bash
# Acil patch release
python scripts/version_manager.py bump patch
git add .
git commit -m "hotfix: critical bug fix"
git tag v0.1.1
git push origin v0.1.1
```

### 3. Rollback Strategy

```bash
# Önceki version'a dön
pip install espocrm-client==0.1.0

# Documentation güncelle
# Known issues belirt
```

## 📋 Prevention Checklist

### Pre-Release
- [ ] Comprehensive testing
- [ ] Security scan
- [ ] Dependency audit
- [ ] Documentation review
- [ ] Version compatibility check

### Release Process
- [ ] Test PyPI validation
- [ ] Automated testing
- [ ] Manual verification
- [ ] Rollback plan ready
- [ ] Monitoring setup

### Post-Release
- [ ] Download monitoring
- [ ] Error tracking
- [ ] User feedback
- [ ] Performance metrics
- [ ] Security updates

## 📞 Support Resources

### Documentation
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

### Community
- [Python Packaging Discord](https://discord.gg/pypa)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/pypi)
- [GitHub Discussions](https://github.com/pypa/packaging-problems/discussions)

### Emergency Contacts
- PyPI Support: admin@pypi.org
- Security Issues: security@python.org

---

**💡 Pro Tip**: Her zaman test environment'da deneme yap ve production'a geçmeden önce tüm kontrolleri yap!