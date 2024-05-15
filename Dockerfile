ARG WHEEL_VER=0.41.0
ARG GRPC_MAX_WORKERS="50"


FROM python:3.11.7 as base
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app


FROM base as poetry
RUN pip install poetry
COPY poetry.lock pyproject.toml /app/
RUN poetry export --without-hashes -o requirements.txt


FROM base as build
COPY --from=poetry /app/requirements.txt /tmp/requirements.txt
RUN python -m venv .venv && \
    .venv/bin/pip install wheel && \
    .venv/bin/pip install -r /tmp/requirements.txt


FROM python:3.11.7-slim as runtime_base
RUN apt update && apt install -y curl git
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
RUN apt install git-lfs -y
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN git lfs install


FROM runtime_base as runtime
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
ENV PATH=/app/.venv/bin:$PATH
ENV GRPC_MAX_WORKERS=${GRPC_MAX_WORKERS}
COPY --from=build /app/.venv /app/.venv
COPY raft_consensus /app/raft_consensus
CMD ["python", "-m", "raft_consensus"]
