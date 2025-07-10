# PyPI Release Plan - EspoCRM Client

## 📋 Genel Bakış

Bu dokümantasyon, EspoCRM Python Client kütüphanesinin PyPI'ye yüklenmesi için gerekli adımları ve süreci detaylandırır.

## 🎯 Hedefler

- [x] Paket adı müsaitlik kontrolü: "espocrm-client" ✅
- [ ] Paket yapılandırmasını güncelle
- [ ] CI/CD pipeline'ı kur
- [ ] Test PyPI'de deneme yap
- [ ] Gerçek PyPI'ye yükle

## 📦 Paket Bilgileri

- **Paket Adı**: `espocrm-client`
- **Mevcut Versiyon**: `0.1.0`
- **Python Desteği**: 3.8+
- **Lisans**: MIT
- **Ana Modül**: `espocrm`

## 🔧 Gerekli Değişiklikler

### 1. Paket Adı Güncellemesi

Aşağıdaki dosyalarda paket adını güncellemek gerekiyor:

- `pyproject.toml` - project.name
- `README.md` - tüm referanslar
- `CHANGELOG.md` - paket adı referansları
- URL'ler ve linkler

### 2. Build Araçları

Gerekli araçlar:
```bash
pip install build twine
```

### 3. GitHub Actions Workflow

`.github/workflows/` dizininde aşağıdaki workflow'ları oluşturmak gerekiyor:

#### a) `ci.yml` - Continuous Integration
- Python 3.8-3.12 testleri
- Farklı işletim sistemleri (Ubuntu, Windows, macOS)
- Code quality checks (black, isort, mypy, flake8)
- Test coverage

#### b) `release.yml` - Release Automation
- Tag oluşturulduğunda tetiklenir
- Test PyPI'ye yükleme
- Gerçek PyPI'ye yükleme
- GitHub Release oluşturma

## 📋 Adım Adım Süreç

### Adım 1: Paket Yapılandırması
```bash
# Paket adını güncelle
# pyproject.toml, README.md, CHANGELOG.md dosyalarını düzenle
```

### Adım 2: Build Araçlarını Kontrol Et
```bash
# Gerekli araçları kur
pip install build twine

# Paket doğrulamasını çalıştır
python scripts/validate_package.py
```

### Adım 3: GitHub Actions Kurulumu
```bash
# .github/workflows/ dizinini oluştur
# CI/CD workflow dosyalarını ekle
```

### Adım 4: PyPI Token Yapılandırması
```bash
# PyPI hesabında API token oluştur
# GitHub Secrets'a ekle:
# - PYPI_API_TOKEN
# - TEST_PYPI_API_TOKEN
```

### Adım 5: Test PyPI Yüklemesi
```bash
# Test PyPI'ye yükle
python -m build
python -m twine upload --repository testpypi dist/*

# Test PyPI'den kur ve test et
pip install --index-url https://test.pypi.org/simple/ espocrm-client
```

### Adım 6: Gerçek PyPI Yüklemesi
```bash
# Gerçek PyPI'ye yükle
python -m twine upload dist/*

# Kurulumu test et
pip install espocrm-client
```

## 🔐 Güvenlik Gereksinimleri

### PyPI API Token
1. PyPI hesabında 2FA aktif olmalı
2. Scoped token kullan (sadece bu proje için)
3. Token'ı GitHub Secrets'da güvenli şekilde sakla

### GitHub Secrets
Aşağıdaki secrets'ları ekle:
- `PYPI_API_TOKEN`: Gerçek PyPI token'ı
- `TEST_PYPI_API_TOKEN`: Test PyPI token'ı

## 📊 Kalite Kontrolleri

### Otomatik Kontroller
- [ ] Syntax validation
- [ ] Import tests
- [ ] Package build test
- [ ] Installation test
- [ ] CLI functionality test
- [ ] Documentation build test

### Manuel Kontroller
- [ ] README.md güncel mi?
- [ ] CHANGELOG.md güncel mi?
- [ ] Version numarası doğru mu?
- [ ] Lisans bilgileri doğru mu?
- [ ] Dependencies güncel mi?

## 🚀 Release Süreci

### 1. Pre-release Hazırlık
```bash
# Version bump
python scripts/version_manager.py bump patch --update-changelog

# Testleri çalıştır
pytest

# Package validation
python scripts/validate_package.py
```

### 2. Release
```bash
# Git tag oluştur
git tag v0.1.0
git push origin v0.1.0

# GitHub Actions otomatik olarak:
# - Test PyPI'ye yükler
# - Testleri çalıştırır
# - Gerçek PyPI'ye yükler
# - GitHub Release oluşturur
```

### 3. Post-release Doğrulama
```bash
# PyPI'den kurulumu test et
pip install espocrm-client

# Temel functionality test
python -c "import espocrm; print(espocrm.__version__)"
```

## 📚 Dokümantasyon Güncellemeleri

### README.md
- Installation instructions
- PyPI badge'leri
- Quick start examples

### CHANGELOG.md
- Release notes
- Breaking changes
- New features

### Documentation Site
- Installation guide
- API reference
- Examples

## 🔄 Sürekli Entegrasyon

### Branch Protection
- `main` branch protected
- PR reviews required
- Status checks required

### Automated Testing
- Python 3.8-3.12
- Ubuntu, Windows, macOS
- Coverage reporting
- Security scanning

## 📈 Monitoring ve Metrics

### PyPI Statistics
- Download counts
- Version adoption
- Geographic distribution

### GitHub Metrics
- Stars, forks, issues
- Community engagement
- Contributor activity

## 🆘 Troubleshooting

### Common Issues
1. **Build Failures**: Check dependencies, Python version
2. **Upload Errors**: Verify API tokens, package name
3. **Import Errors**: Check package structure, __init__.py
4. **Version Conflicts**: Ensure unique version numbers

### Support Channels
- GitHub Issues
- Documentation
- Community discussions

## ✅ Checklist

### Pre-release
- [ ] Paket adı güncellendi
- [ ] Version numarası güncellendi
- [ ] CHANGELOG.md güncellendi
- [ ] Testler geçiyor
- [ ] Documentation güncel
- [ ] GitHub Actions kuruldu

### Release
- [ ] Test PyPI yüklemesi başarılı
- [ ] Test PyPI'den kurulum test edildi
- [ ] Gerçek PyPI yüklemesi başarılı
- [ ] GitHub Release oluşturuldu
- [ ] Documentation deploy edildi

### Post-release
- [ ] PyPI'den kurulum doğrulandı
- [ ] Community bilgilendirildi
- [ ] Next version planning başladı

---

**Not**: Bu plan, projenin PyPI'ye güvenli ve profesyonel bir şekilde yüklenmesini sağlamak için tasarlanmıştır. Her adım dikkatli şekilde takip edilmelidir.