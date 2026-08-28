#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name="agenthub",
    version="0.1.0",
    author="",
    author_email="",
    description="couple of ai agents to find error in your ai",
    install_requires=["dspy", "openai==1.55.3", "chromadb", "sentence-transformers"],
    extras_require={},
    packages=find_packages(exclude=("archive", "configs", "experiments", "tests")),
)
