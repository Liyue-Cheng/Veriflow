# file: setup.py
from setuptools import setup, find_packages

setup(
    name="veriflow",
    version="0.1.0",
    author="Liyue Cheng",
    author_email="liyue_cheng@163.com",
    description="A comprehensive Python-based digital circuit verification and simulation framework.",
    # long_description=open("README.md", encoding="utf-8").read(),
    # long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        "numpy>=1.20.0",
        "bitstring>=3.1.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: Software Development :: Testing",
    ],
    keywords="verilog simulation verification digital-circuit eda",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/veriflow/issues",
        "Source": "https://github.com/yourusername/veriflow",
    },
) 