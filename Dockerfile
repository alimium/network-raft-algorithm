ARG POETRY_VER=1.8.2
ARG WHEEL_VER=0.41.0


FROM python:3.11.7 as base
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app


FROM base as poetry
RUN pip install poetry==${POETRY_VER}
COPY poetry.lock pyproject.toml /app/
RUN poetry export --without-hashes -o requirements.txt


FROM base as build
COPY --from=poetry /app/requirements.txt /tmp/requirements.txt
RUN python -m venv .venv && \
    .venv/bin/pip install 'wheel==${WHEEL_VER}' && \
    .venv/bin/pip install -r /tmp/requirements.txt


FROM python:3.11.7-slim as runtime
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
ENV PATH=/app/.venv/bin:$PATH
COPY --from=build /app/.venv /app/.venv
COPY raft-consensus /app/raft-consensus
CMD ["python", "-m", "raft-consensus"]
