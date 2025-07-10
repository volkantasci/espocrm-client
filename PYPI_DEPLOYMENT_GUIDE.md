# PyPI Deployment Guide - EspoCRM Client

## 🚀 Hızlı Başlangıç

Bu rehber, EspoCRM Client paketini PyPI'ye yüklemek için gereken tüm adımları içerir.

## 📋 Ön Gereksinimler

### 1. Sistem Gereksinimleri
```bash
# Python 3.8+ gerekli
python --version

# Git kurulu olmalı
git --version
```

### 2. Gerekli Araçları Kur
```bash
# Build ve upload araçları
pip install --upgrade pip
pip install build twine

# Development dependencies
pip install -e ".[dev]"
```

### 3. PyPI Hesap Kurulumu

#### PyPI Hesabı
1. https://pypi.org/account/register/ adresinden hesap oluştur
2. Email doğrulaması yap
3. 2FA (Two-Factor Authentication) aktifleştir

#### Test PyPI Hesabı
1. https://test.pypi.org/account/register/ adresinden hesap oluştur
2. Email doğrulaması yap

#### API Token Oluşturma
```bash
# PyPI'de API token oluştur:
# 1. Account settings > API tokens
# 2. "Add API token" tıkla
# 3. Token name: "espocrm-client"
# 4. Scope: "Entire account" (ilk yükleme için)
# 5. Token'ı güvenli bir yerde sakla
```

## 🔧 Paket Hazırlığı

### 1. Paket Adını Güncelle

**pyproject.toml**
```toml
[project]
name = "espocrm-client"  # "espocrm-python-client" yerine
```

**README.md**
```markdown
# EspoCRM Client

pip install espocrm-client  # Güncellenen paket adı
```

### 2. Version Kontrolü
```bash
# Mevcut versiyonu kontrol et
python scripts/version_manager.py current

# Gerekirse version bump yap
python scripts/version_manager.py bump patch --update-changelog
```

### 3. Paket Doğrulaması
```bash
# Tüm validasyonları çalıştır
python scripts/validate_package.py

# Hızlı validasyon (build ve install skip)
python scripts/validate_package.py --skip-build --skip-install
```

## 🏗️ Build Süreci

### 1. Temizlik
```bash
# Eski build dosyalarını temizle
rm -rf build/ dist/ *.egg-info/

# Cache temizliği
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete
```

### 2. Package Build
```bash
# Package'ı build et
python -m build

# Build çıktısını kontrol et
ls -la dist/
# Beklenen dosyalar:
# - espocrm_client-0.1.0-py3-none-any.whl
# - espocrm-client-0.1.0.tar.gz
```

### 3. Package Doğrulaması
```bash
# Twine ile package'ı kontrol et
python -m twine check dist/*

# Detaylı kontrol
python -m twine check --strict dist/*
```

## 🧪 Test PyPI Yüklemesi

### 1. Test PyPI'ye Upload
```bash
# Test PyPI'ye yükle
python -m twine upload --repository testpypi dist/*

# Username: __token__
# Password: [TEST_PYPI_API_TOKEN]
```

### 2. Test PyPI'den Kurulum Testi
```bash
# Yeni virtual environment oluştur
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
# test_env\Scripts\activate  # Windows

# Test PyPI'den kur
pip install --index-url https://test.pypi.org/simple/ \
           --extra-index-url https://pypi.org/simple/ \
           espocrm-client

# Import testi
python -c "import espocrm; print(f'Version: {espocrm.__version__}')"

# CLI testi
espocrm-cli --version

# Temizlik
deactivate
rm -rf test_env
```

## 🚀 Production PyPI Yüklemesi

### 1. Final Kontroller
```bash
# Son kez testleri çalıştır
pytest

# Package validation
python scripts/validate_package.py

# Git durumu kontrol et
git status
git log --oneline -5
```

### 2. Git Tag Oluştur
```bash
# Version tag oluştur
git tag v0.1.0
git push origin v0.1.0

# Tag'leri listele
git tag -l
```

### 3. PyPI'ye Upload
```bash
# Production PyPI'ye yükle
python -m twine upload dist/*

# Username: __token__
# Password: [PYPI_API_TOKEN]
```

### 4. Yükleme Doğrulaması
```bash
# Birkaç dakika bekle (PyPI propagation)
sleep 120

# Yeni virtual environment
python -m venv verify_env
source verify_env/bin/activate

# PyPI'den kur
pip install espocrm-client

# Functionality test
python -c "
import espocrm
from espocrm.auth import APIKeyAuth
print(f'Successfully installed espocrm-client v{espocrm.__version__}')
"

# Temizlik
deactivate
rm -rf verify_env
```

## 🔐 Güvenlik En İyi Uygulamaları

### 1. API Token Güvenliği
```bash
# Token'ları environment variable olarak sakla
export PYPI_API_TOKEN="pypi-..."
export TEST_PYPI_API_TOKEN="pypi-..."

# .pypirc dosyası kullanma (güvenlik riski)
```

### 2. Scoped Tokens
```bash
# İlk yüklemeden sonra scoped token oluştur:
# 1. PyPI'de package sayfasına git
# 2. Manage > Settings > API tokens
# 3. "Add API token" - sadece bu proje için
```

### 3. GitHub Secrets
```bash
# GitHub repository settings'de secrets ekle:
# - PYPI_API_TOKEN
# - TEST_PYPI_API_TOKEN
```

## 🔄 Otomatik Deployment (GitHub Actions)

### 1. Workflow Kurulumu
```bash
# .github/workflows/ dizinini oluştur
mkdir -p .github/workflows

# Workflow dosyalarını ekle (GITHUB_ACTIONS_WORKFLOWS.md'den)
```

### 2. Manual Release
```bash
# Tag push ile otomatik release
git tag v0.1.1
git push origin v0.1.1

# GitHub Actions otomatik olarak:
# 1. Test PyPI'ye yükler
# 2. Testleri çalıştırır  
# 3. Production PyPI'ye yükler
# 4. GitHub Release oluşturur
```

## 📊 Post-Release Aktiviteler

### 1. Monitoring
```bash
# PyPI statistics
# https://pypi.org/project/espocrm-client/

# Download stats
# https://pypistats.org/packages/espocrm-client
```

### 2. Documentation Update
```bash
# README badges güncelle
# Installation instructions kontrol et
# Documentation site deploy et
```

### 3. Community Notification
```bash
# GitHub Release notes
# Social media announcement
# Community forums
```

## 🆘 Troubleshooting

### Common Issues

#### 1. Package Name Conflict
```bash
# Error: Package name already exists
# Solution: Farklı bir isim seç veya mevcut maintainer'dan izin al
```

#### 2. Upload Permission Denied
```bash
# Error: 403 Forbidden
# Solution: API token'ı kontrol et, scope'u doğrula
```

#### 3. Build Failures
```bash
# Error: Build failed
# Solution: Dependencies kontrol et, Python version uyumluluğu
```

#### 4. Import Errors
```bash
# Error: ModuleNotFoundError
# Solution: Package structure kontrol et, __init__.py dosyaları
```

### Debug Commands
```bash
# Verbose upload
python -m twine upload --verbose dist/*

# Check package contents
python -m zipfile -l dist/*.whl

# Test import in isolation
python -c "import sys; print(sys.path); import espocrm"
```

## 📋 Checklist

### Pre-Release
- [ ] Paket adı güncellendi
- [ ] Version numarası doğru
- [ ] CHANGELOG.md güncellendi
- [ ] Testler geçiyor
- [ ] Package validation başarılı
- [ ] Git tag oluşturuldu

### Test PyPI
- [ ] Test PyPI upload başarılı
- [ ] Test PyPI'den kurulum başarılı
- [ ] Import ve CLI testleri geçiyor

### Production PyPI
- [ ] Production PyPI upload başarılı
- [ ] PyPI'den kurulum doğrulandı
- [ ] GitHub Release oluşturuldu
- [ ] Documentation güncellendi

### Post-Release
- [ ] Download stats monitoring
- [ ] Community feedback
- [ ] Issue tracking
- [ ] Next version planning

---

**🎉 Tebrikler!** EspoCRM Client paketiniz artık PyPI'de yayında ve herkes tarafından kullanılabilir durumda!

```bash
pip install espocrm-client