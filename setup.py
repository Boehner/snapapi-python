"""
Minimal setuptools config for snapapi-python.

Install from source:
    pip install .

Install in editable/dev mode:
    pip install -e .

Publish to PyPI:
    python setup.py sdist bdist_wheel
    twine upload dist/*
"""

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="snapapi-python",
    version="0.1.1",
    description="Python SDK for the SnapAPI web intelligence API — screenshots, metadata, PDF, page analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SnapAPI",
    author_email="hello@snapapi.tech",
    url="https://snapapi.tech",
    project_urls={
        "Documentation": "https://snapapi.tech/docs",
        "Source":        "https://github.com/Boehner/snapapi-python",
        "Bug Tracker":   "https://github.com/Boehner/snapapi-python/issues",
    },
    py_modules=["snapapi"],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="screenshot api web-scraping metadata pdf puppeteer snapapi",
    license="MIT",
)
