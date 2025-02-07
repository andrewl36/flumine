import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "requirements.txt")) as f:
    INSTALL_REQUIRES = f.read().splitlines()

about = {}
with open(os.path.join(here, "flumine", "__version__.py"), "r") as f:
    exec(f.read(), about)

setup(
    name=about["__title__"],
    version=about["__version__"],
    packages=find_packages(
        exclude=[
            "examples",
            "examples.strategies",
            "examples.workers",
            "examples.middleware",
            "examples.controls",
        ]
    ),
    package_dir={"flumine": "flumine"},
    install_requires=INSTALL_REQUIRES,
    url=about["__url__"],
    license=about["__license__"],
    author=about["__author__"],
    author_email="a@unknown.invalid",
    description=about["__description__"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    test_suite="tests",
)
