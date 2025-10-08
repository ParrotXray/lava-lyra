import re
import setuptools
from pathlib import Path


classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Framework :: AsyncIO",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: Implementation :: CPython",
    "Topic :: Communications",
    "Topic :: Communications :: Chat",
    "Topic :: Internet",
    "Topic :: Multimedia :: Sound/Audio",
    "Topic :: Software Development",
    "Topic :: Software Development :: Libraries",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Networking",
    "Typing :: Typed",
]

extras_require = {
    "docs": [
        "sphinx>=5.0.0",
        "sphinx-rtd-theme>=1.0.0",
        "sphinxcontrib-asyncio>=0.3.0",
    ],
    "dev": [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.20.0",
        "mypy>=0.991",
        "black>=22.0.0",
        "isort>=5.10.0",
        "flake8>=5.0.0",
        "pre-commit>=2.20.0",
    ],
    "speed": [
        "aiohttp[speedups]",
        "cchardet",
        "aiodns",
        "orjson",
    ],
}

install_requires = [
    "aiohttp>=3.8.0",
    "orjson>=3.8.0",
    "websockets>=10.0",
    "typing-extensions;python_version<'3.11'",
    "py-cord>=2.0.0",
]

packages = setuptools.find_packages(include=["lava_lyra", "lava_lyra.*"])

project_urls = {
    "Homepage": "https://github.com/ParrotXray/lava-lyra",
    # "Documentation": "https://lava-lyra.readthedocs.io/",
    "Issue Tracker": "https://github.com/ParrotXray/lava-lyra/issues",
    "Source": "https://github.com/ParrotXray/lava-lyra",
    "Changelog": "https://github.com/ParrotXray/lava-lyra/blob/main/CHANGELOG.md",
    "Original Pomice": "https://github.com/cloudwithax/pomice",
}

_version_regex = r"^__version__ = ['\"]([^'\"]*)['\"]$"

init_file = Path("lava_lyra/__init__.py")
if init_file.exists():
    with open(init_file, encoding="utf-8") as stream:
        match = re.search(_version_regex, stream.read(), re.MULTILINE)
        if match:
            version = match.group(1)
        else:
            raise RuntimeError("Cannot find version string in __init__.py")
else:
    version = "1.0.0"

if "dev" in version or "alpha" in version or "beta" in version or "rc" in version:
    try:
        import subprocess
        
        process = subprocess.Popen(
            ["git", "rev-list", "--count", "HEAD"], 
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        out, _ = process.communicate()
        if out and process.returncode == 0:
            commit_count = out.decode("utf-8").strip()
            version += f".dev{commit_count}"

        process = subprocess.Popen(
            ["git", "rev-parse", "--short", "HEAD"], 
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        out, _ = process.communicate()
        if out and process.returncode == 0:
            short_hash = out.decode("utf-8").strip()
            version += f"+g{short_hash}"
            
    except (Exception, FileNotFoundError):
        pass

readme_file = Path("README.md")
if readme_file.exists():
    with open(readme_file, encoding="utf-8") as f:
        long_description = f.read()
    long_description_content_type = "text/markdown"
else:
    long_description = "A modern Lavalink v4 wrapper for py-cord, based on Pomice."
    long_description_content_type = "text/plain"

setuptools.setup(
    name="lava-lyra",
    version=version,
    author="ParrotXray",
    author_email="",
    description="A modern Lavalink v4 wrapper for py-cord, based on Pomice",
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    url="https://github.com/ParrotXray/lava-lyra",
    project_urls=project_urls,
    packages=packages,
    classifiers=classifiers,
    python_requires=">=3.10",
    install_requires=install_requires,
    extras_require=extras_require,
    license="GPL-3.0",
    keywords="discord lavalink py-cord music audio bot lavalink4 voice streaming",
    include_package_data=True,
    zip_safe=False,
    package_data={
        "lava_lyra": ["py.typed"],
    },
)