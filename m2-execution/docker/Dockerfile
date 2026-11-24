FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+pinned.0aa7ce6

RUN useradd --create-home --uid 10001 runner

WORKDIR /app

COPY docker/requirements.lock docker/build-requirements.lock /tmp/
RUN pip install --require-hashes -r /tmp/requirements.lock \
 && pip install --require-hashes -r /tmp/build-requirements.lock

COPY upstream/black/ /app/
# No fallback with "||": a failed install must fail the build, not be hidden.
RUN pip install --no-deps --no-build-isolation -e .

RUN chown -R runner:runner /app
USER runner

CMD ["pytest", "--version"]