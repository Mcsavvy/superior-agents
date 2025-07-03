from setuptools import setup, find_packages

setup(
    name="poolmind_agent",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "langchain>=0.0.267",
        "langchain-core>=0.1.0",
        "langgraph>=0.0.15",
        "chromadb>=0.4.15",
        "openai>=1.0.0",
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
    ],
    extras_require={
        "dev": [
            "black",
            "isort",
            "flake8",
            "mypy",
        ],
        "test": [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "httpx",
        ],
    },
    description="PoolMind AI Agent for cross-exchange arbitrage trading",
    author="PoolMind Team",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
