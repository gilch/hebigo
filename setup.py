#!/usr/bin/env python3
import setuptools


with open("README.md", encoding="utf8") as f:
    long_description = f.read()


setuptools.setup(
    name="hebigo",
    version="0.1.0",
    description="An indentation-based skin for Hissp.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Matthew Egan Odendahl",
    author_email="hissp.gilch@xoxy.net",
    license="Apache-2.0",
    url="https://github.com/gilch/hebigo",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Libraries",
    ],
    keywords="macro metaprogramming compiler DSL AST transpiler",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    install_requires=["hissp", "jupyter-console"],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["hebi=hebi.__main__:main"]},
)
