"""
Setup configuration for agentic-test CLI package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README if it exists
readme_file = Path("README.md")
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "AI-powered test generation with multi-agent orchestration"

setup(
    name="agentic-test",
    version="0.1.0",
    description="AI-powered test generation with multi-agent orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/agentic-testing",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.18.0",
        "click>=8.0.0",
        "colorama>=0.4.6",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "langchain>=0.1.0",
        "langchain-anthropic>=0.1.0",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "python-multipart>=0.0.6",
        "aiofiles>=23.0.0",
    ],
    entry_points={
        "console_scripts": [
            "agentic-test=agentic_test.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="testing, ai, claude, anthropic, pytest, test-generation, agentic",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/agentic-testing/issues",
        "Source": "https://github.com/yourusername/agentic-testing",
        "Documentation": "https://github.com/yourusername/agentic-testing#readme",
    },
)

