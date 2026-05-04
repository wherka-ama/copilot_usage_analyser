from setuptools import setup, find_packages

setup(
    name="copilot-usage-analyser",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic>=2.0",
        "python-dateutil>=2.8",
        "click>=8.0",
        "rich>=13.0",
        "matplotlib>=3.7",
    ],
    entry_points={
        "console_scripts": [
            "cua=copilot_usage_analyser.cli.main:cli",
        ],
    },
)
