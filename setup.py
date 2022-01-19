"""Setup pgmvt."""

from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "asyncpg>=0.23.0",
    "buildpg>=0.3",
    "starlite>=0.5",
    "jinja2>=2.11.2,<3.0.0",
    "morecantile>=3.0.2,<3.1",
    "importlib_resources>=1.1.0;python_version<'3.9'",
]

test_reqs = [
    "pytest",
    "pytest-cov",
    "pytest-asyncio",
    "requests",
    "psycopg2",
    "pytest-pgsql",
    "mapbox-vector-tile",
    "numpy",
]

# "morecantile>=3.0.2,<3.1",
extra_reqs = {
    "test": test_reqs,
    "dev": test_reqs + ["pre-commit"],
    "server": ["uvicorn[standard]"],
    "docs": [
        "nbconvert",
        "mkdocs",
        "mkdocs-material",
        "mkdocs-jupyter",
        "pygments",
        "pdocs",
    ],
}


setup(
    name="pg_mvt",
    description=u"",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="FastAPI MVT POSTGIS",
    author=u"Vincent Sarago",
    author_email="vincent@developmentseed.org",
    url="https://github.com/developmentseed/pg_mvt",
    license="MIT",
    packages=find_packages(exclude=["tests*"]),
    package_data={"pg_mvt": ["templates/*.html"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
