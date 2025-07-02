# Installation Guide

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **EspoCRM**: Version 6.0 or higher with API access enabled

## Install from PyPI (Recommended)

The easiest way to install EspoCRM Python Client is from PyPI using pip:

```bash
pip install espocrm-python-client
```

### Verify Installation

```bash
python -c "import espocrm; print(f'EspoCRM Python Client v{espocrm.__version__} installed successfully!')"
```

### Test CLI Tool

```bash
espocrm-cli --version
```

## Install from Source

If you want to install the latest development version or contribute to the project:

```bash
git clone https://github.com/espocrm/espocrm-python-client.git
cd espocrm-python-client
pip install -e .
```

## Optional Dependencies

### Async Support

For asynchronous operations support:

```bash
pip install espocrm-python-client[async]
```

This includes:
- `httpx>=0.25.0` - Async HTTP client
- `aiofiles>=23.2.0` - Async file operations

### Documentation Tools

For building documentation locally:

```bash
pip install espocrm-python-client[docs]
```

This includes:
- `mkdocs>=1.5.0` - Documentation generator
- `mkdocs-material>=9.4.0` - Material theme
- `mkdocstrings[python]>=0.24.0` - API documentation

### Development Tools

For development and testing:

```bash
pip install espocrm-python-client[dev]
```

This includes all development dependencies:
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `black>=23.0.0` - Code formatting
- `isort>=5.12.0` - Import sorting
- `mypy>=1.7.0` - Type checking
- `flake8>=6.0.0` - Linting
- `bandit>=1.7.0` - Security scanning
- `pre-commit>=3.5.0` - Git hooks

### All Optional Dependencies

To install all optional dependencies at once:

```bash
pip install espocrm-python-client[async,docs,dev]
```

## Virtual Environment (Recommended)

It's recommended to use a virtual environment to avoid conflicts with other packages:

### Using venv

```bash
# Create virtual environment
python -m venv espocrm-env

# Activate virtual environment
# On Windows:
espocrm-env\Scripts\activate
# On macOS/Linux:
source espocrm-env/bin/activate

# Install the package
pip install espocrm-python-client

# Deactivate when done
deactivate
```

### Using conda

```bash
# Create conda environment
conda create -n espocrm-env python=3.11

# Activate environment
conda activate espocrm-env

# Install the package
pip install espocrm-python-client

# Deactivate when done
conda deactivate
```

## Docker Installation

You can also use Docker to run the client in a containerized environment:

```dockerfile
FROM python:3.11-slim

# Install the client
RUN pip install espocrm-python-client

# Set working directory
WORKDIR /app

# Copy your application code
COPY . .

# Run your application
CMD ["python", "your_app.py"]
```

Build and run:

```bash
docker build -t espocrm-app .
docker run -e ESPOCRM_URL="https://your-espocrm.com" -e ESPOCRM_API_KEY="your-key" espocrm-app
```

## Troubleshooting

### Common Issues

#### ImportError: No module named 'espocrm'

This usually means the package wasn't installed correctly. Try:

```bash
pip install --upgrade espocrm-python-client
```

#### SSL Certificate Issues

If you encounter SSL certificate errors:

```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org espocrm-python-client
```

#### Permission Errors

On some systems, you might need to use `--user` flag:

```bash
pip install --user espocrm-python-client
```

#### Version Conflicts

If you have dependency conflicts, try upgrading pip and setuptools:

```bash
pip install --upgrade pip setuptools
pip install espocrm-python-client
```

### Platform-Specific Notes

#### Windows

- Make sure Python is added to your PATH
- You might need to use `py` instead of `python`
- Consider using Windows Subsystem for Linux (WSL) for better compatibility

#### macOS

- If using Homebrew Python, make sure it's properly configured
- You might need to install Xcode command line tools: `xcode-select --install`

#### Linux

- Some distributions require `python3-pip` package
- On Ubuntu/Debian: `sudo apt-get install python3-pip`
- On CentOS/RHEL: `sudo yum install python3-pip`

### Getting Help

If you encounter issues during installation:

1. Check the [GitHub Issues](https://github.com/espocrm/espocrm-python-client/issues)
2. Create a new issue with:
   - Your operating system and version
   - Python version (`python --version`)
   - pip version (`pip --version`)
   - Complete error message
   - Steps to reproduce

## Next Steps

After successful installation:

1. [Configure your EspoCRM connection](configuration.md)
2. [Set up authentication](authentication.md)
3. [Try the quick start guide](quickstart.md)
4. [Explore the CLI tool](cli.md)

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade espocrm-python-client
```

To upgrade to a specific version:

```bash
pip install espocrm-python-client==1.2.3
```

Check your current version:

```bash
python -c "import espocrm; print(espocrm.__version__)"
```

## Uninstalling

To remove the package:

```bash
pip uninstall espocrm-python-client