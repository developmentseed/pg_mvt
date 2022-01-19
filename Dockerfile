ARG PYTHON_VERSION=3.8

FROM ghcr.io/vincentsarago/uvicorn-gunicorn:${PYTHON_VERSION}

WORKDIR /tmp

COPY README.md README.md
COPY pg_mvt/ pg_mvt/
COPY setup.py setup.py

RUN pip install . --no-cache-dir
RUN rm -rf pg_mvt/ README.md setup.py

ENV MODULE_NAME pg_mvt.main
ENV VARIABLE_NAME app
