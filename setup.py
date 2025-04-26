from setuptools import setup, find_packages
# import os

# Read the contents of README.md
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="mac-file-organizer",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "watchdog",  # For file system monitoring
        "pyobjc-framework-Cocoa",  # For macOS integration
    ],
    entry_points={
        "console_scripts": [
            "mac-file-organizer=mac_file_organizer.__main__:main",
        ],
    },
    package_data={
        "": ["resources/*.json", "resources/*.plist"],
    },
    author="V",
    author_email="V_@smth.com",
    description="A daemon for automatically organizing files in Downloads and Desktop folders on macOS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="macos, file, organization, daemon",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: MacOS :: MacOS X",
        "Topic :: Desktop Environment :: File Managers",
        "Topic :: Utilities",
    ],
)