from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mailstream",
    version="0.1.2",
    author="Christian Obora",
    author_email="christianobora@uchicago.edu",
    description="Async IMAP client for streaming email messages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/christianobora/mailstream",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Communications :: Email",
    ],
    python_requires=">=3.8",
    install_requires=["aioimaplib>=1.0.1"],
    extras_require={
        "dev": [
            "pytest>=8.3.4",
            "pytest-asyncio>=0.16.0",
            "mypy>=1.0.0",
            "black>=24.10.0",
            "flake8>=4.0.0",
        ],
        "examples": [
            "openai>=0.11.0",
            "beautifulsoup4>=4.10.0",
        ],
    },
    keywords="imap email streaming library",
)