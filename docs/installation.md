# Installation Guide

## Prerequisites

- Python 3.8+
- pip package manager

## Install from PyPI

```bash
pip install mailstream
```

## Install from Source

```bash
# Clone the repository
git clone https://github.com/christianobora/mailstream.git

# Change directory
cd mailstream

# Install in editable mode
pip install -e .

# Install development dependencies
pip install -e .[dev]
```

## Verify Installation

```python
import mailstream
print(mailstream.__version__)
```

## Potential Issues

### SSL Certification
If you encounter SSL certificate issues, ensure your system's CA certificates are up to date.

### Firewall Configuration
Ensure your firewall allows outbound connections on port 993 (IMAP SSL).