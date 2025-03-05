from setuptools import setup, find_packages

setup(
    name="wattleflow",
    version="0.0.0.5",
    description="Wattleflow Core for Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="wattleFlow",
    author_email="wattleflow@outlook.com",
    url="https://github.com/wattleflow/core.git",
    license="Apache-2.0",
    packages=find_packages(where="src"),
    package_dir={"src": "src/wattleflow"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.7.1",
    install_requires=[
        "setuptools>=65.6.3"
    ],
)
