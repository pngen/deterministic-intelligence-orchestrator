from setuptools import setup, find_packages

setup(
    name="dio",
    version="1.0.0",
    description="Deterministic Intelligence Orchestrator",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies for core functionality
        # All using Python stdlib
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'mypy>=1.0.0',
            'black>=23.0.0',
        ],
        'logging': [
            'python-json-logger>=2.0.0',  # For structured logging
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)