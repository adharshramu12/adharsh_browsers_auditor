from setuptools import setup, find_packages

setup(
    name="adharsh-browser-auditor",
    version="1.0.0",
    author="Adharsh Kumar Bachu",
    description="A premium, enterprise-grade browser data extraction and management tool.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/adharsh-browser-auditor",
    packages=find_packages(),
    install_requires=[
        "customtkinter",
        "sqlite3; python_version < '3'",  # sqlite3 is usually built-in
    ],
    entry_points={
        "console_scripts": [
            "auditor=gui:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.7",
)
